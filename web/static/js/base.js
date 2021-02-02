// Init sidebar accordion
$('.ui.accordion')
    .accordion()
    ;

// Sidebar stuff
function onResize() {

    if ($('.ui.top.fixed.menu').length == 1) {
        $('.ui.top.fixed.menu').css('z-index', 101);
        $('.ui.sidenav.menu').css('z-index', 102);

        $('.ui.sidenav.menu').css('top', $('.ui.top.fixed.menu').outerHeight() + 'px');
        $('.ui.sidenav.menu').css('height', ($(window).height() - $('.ui.top.fixed.menu').outerHeight()) + 'px');

        $('.ui.sidenav.menu').next().css('padding-top', $('.ui.top.fixed.menu').outerHeight() + 'px');
    }

    $('.ui.sidenav.menu .sidenav-inner-wrap').css('width', '');

    if ($(window).width() > 768) {
        $('.mobile-only').hide();

        $('.ui.sidenav.menu').next().css('margin-left', $('.ui.sidenav.menu').outerWidth() + 'px');
        $('.ui.sidenav.menu').css('width', '15rem');
        $('.ui.sidenav .compact-menu, .ui.sidenav .expand-menu').show();
    } else {
        $('.ui.sidenav.menu').next().css('margin-left', $('.ui.sidenav.menu').outerWidth() + 'px');
        $('.ui.sidenav').removeClass('compact-menu').addClass('expand-menu');
        $('.ui.sidenav').find('.icon').removeClass('left').addClass('right');
        $('.ui.sidenav').addClass('compact').addClass('icon');
        $('.ui.sidenav .item:has(.menu)').addClass('zero-padding');

        localStorage.setItem('sidebarState', 'collapse');
    }

    // igv.visibilityChange();

};


$(document).ready(function () {
    var collapseTrigger = '.ui.sidenav .compact-menu';
    var expandTrigger = '.ui.sidenav .expand-menu';
    var openMobileNavTrigger = '.ui.top.fixed .open-mobile-nav';
    var closeMobileNavTrigger = '.ui.sidenav .close-mobile-nav';

    $(document).on('click', collapseTrigger, function () {
        $(this).removeClass('compact-menu').addClass('expand-menu');
        $(this).find('.icon').removeClass('left').addClass('right');
        $('.ui.sidenav').addClass('compact').addClass('icon');
        $('.ui.sidenav .item:has(.menu)').addClass('zero-padding');

        localStorage.setItem('sidebarState', 'collapse');

        onResize();
    });

    $(document).on('click', expandTrigger, function () {
        $(this).removeClass('expand-menu').addClass('compact-menu');
        $(this).find('.icon').removeClass('right').addClass('left');
        $('.ui.sidenav').removeClass('compact').removeClass('icon');
        $('.ui.sidenav .item:has(.menu)').removeClass('zero-padding');

        localStorage.setItem('sidebarState', 'expand');

        onResize();
    });

    $(document).on('click', openMobileNavTrigger, function () {
        $('.ui.sidenav').addClass('menu-open').show();
    });

    $(document).on('click', closeMobileNavTrigger, function () {
        $('.ui.sidenav').removeClass('menu-open').hide();
    });

    window.addEventListener('resize', onResize);
    onResize();

    // $('.ui.accordion').accordion();

});

let sidebarState = localStorage.getItem('sidebarState')
if (sidebarState === 'collapse') {
    $('.ui.sidenav .compact-menu').removeClass('compact-menu').addClass('expand-menu');
    $('.ui.sidenav .expand-menu').find('.icon').removeClass('left').addClass('right');
    $('.ui.sidenav').addClass('compact').addClass('icon');
    $('.ui.sidenav .item:has(.menu)').addClass('zero-padding');

    onResize();
}