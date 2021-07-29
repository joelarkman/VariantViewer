from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


@shared_task(bind=True)
def send_email(self, email_type, context, subject, to):
    try:
        # fetch context models
        context_raw = context.copy()
        print(context_raw)
        context = {}
        for k, v in context_raw.items():
            if isinstance(v, dict) and v.get('model'):
                app_label, model_name = v.get('model')
                model = apps.get_model(
                    app_label=app_label,
                    model_name=model_name
                )
                obj = None
                if v.get('id'):
                    obj = model.objects.get(id=v['id'])
                elif v.get('list'):
                    obj = [model.objects.get(id=x) for x in v['list']]
                context[k] = obj
            else:
                context[k] = v
        # set up email content
        plaintext = get_template(f'emails/{email_type}/{email_type}.txt')
        text_content = plaintext.render(context)

        from_email = settings.SERVER_EMAIL
        if isinstance(to, str):
            to = [to]

        # prepare and send email
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.send()
    except Exception as e:
        retry_time = 2 ** self.request.retries
        print(f"Failed with exception {e}.")
        print(f"Retrying in {retry_time}")
        self.retry(countdown=retry_time)
