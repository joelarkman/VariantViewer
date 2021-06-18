// =========
// MAIN TABS 
// ========= 

$(document).ready(function () {

    $('.main-tabs-link').click(function () {
        var tab_id = $(this).attr('data-tab');

        $('.main-tabs-link').removeClass('active');
        $('.main-tabs-content').removeClass('active');
        $('.main-tabs-content').addClass('hidden');

        $(this).addClass('active');
        $("#" + tab_id).addClass('active');
        $("#" + tab_id).removeClass('hidden');

        $('.main-tabs-content').hide().filter(".active").show()

        $.fn.dataTable
            .tables({ visible: true, api: true })
            .columns.adjust()
            .draw();

        $(".dataTables_scrollHeadInner").css("width", "100%");
    })

})

// Hide non-active tabs initially
$('.main-tabs-content').hide().filter(".active").show()


// =================
// UTILITY FUNCTIONS 
// ================= 

function ResetHideBrowser() {
    $('#variants-main-panel').show();
    $("#browser-expand-collapse").removeClass("primary")
    $('#browser-expand-collapse .icon').addClass("expand").removeClass("compress")
    $("#browser-expand-collapse").attr("data-tooltip", "Expand Browser");
    $('#browser').addClass("browser-collapsed").removeClass("browser-expanded");
    $('.view-in-browser').attr("data-tooltip", "Show Browser");
    $('#browser').hide();
    $('#browser-expand-collapse').hide()
    $('.view-in-browser').removeClass("red");
}

// =================
// LOAD VARIANT LIST
// =================
$(function () {
    $.ajax(
        {
            type: 'get',
            url: $('#variant-menu').attr('data-url'), //get url from toggle attribute
            beforeSend: function () {
                // Load a loading circle if taking more than 3ms
                ajaxLoadTimeout = setTimeout(function () {
                    $("#variant-list-content-loader").addClass('active');
                }, 20);
            },
            success: function (data) {

                // Use returned data to update the unpinned and pinned lists of variants. 
                // This is done individually to retain search term and scroll positions.
                $('#variant-menu').append(data.variant_list)
                $('#variants-tab #tab-utility-bar .filters-sub-menu-container').html(data.active_filters)
                SetupFilterScrolling()

                clearTimeout(ajaxLoadTimeout);
                $("#variant-list-content-loader").removeClass('active');

                // Refresh popups
                $("#variant-menu .js-update-transcript,.pinned-transcript-popup").popup({
                    inline: false
                })

            },
            error: function () {
                alert("error");
            }
        })
})


// ==============
// VARIANT FILTER 
// ============== 

// Filters scroll
function SetupFilterScrolling() {

    // Make buttons scroll filters bar id the buttons are not disabled
    $('#right-button').click(function () {
        if (!$(this).hasClass("disabled")) {
            $('.active-filters-container').animate({
                scrollLeft: "+=150px"
            }, "500");
        }


    });

    $('#left-button').click(function () {
        if (!$(this).hasClass("disabled")) {
            $('.active-filters-container').animate({
                scrollLeft: "-=150px"
            }, "500");
        }
    });

    // Code to grey out arrows at each extreme
    jQuery(function ($) {
        $('.active-filters-container').on('scroll', function () {
            if (($(this).scrollLeft() + $(this).innerWidth()) >= $(this)[0].scrollWidth - 0.5) { //when fully scrolled right
                $('#right-ellipses').hide()
                $('#left-ellipses').show()
                $('#right-button').addClass('disabled');
                $('#left-button').removeClass('disabled');
            } else if ($(this).scrollLeft() === 0) { // when fully scrolled left
                $('#left-ellipses').hide()
                $('#right-ellipses').show()
                $('#left-button').addClass('disabled');
                $('#right-button').removeClass('disabled');
            } else {
                $('#right-ellipses').hide()
                $('#left-ellipses').show()
                $('#right-button').removeClass('disabled');
                $('#left-button').removeClass('disabled');
            }

            // For troubleshooting!
            // console.log($('#testing123').scrollLeft() + $('#testing123').innerWidth())
            // console.log($('#testing123')[0].scrollWidth)
        })
    });

    $(window).on('resize', function () {
        if ($('.active-filters-container')[0]) {
            if ($('.active-filters-container')[0].offsetWidth < $('.active-filters-container')[0].scrollWidth) {
                $('#left-ellipses').hide()
                $('#right-ellipses').show()
                $('#right-button').removeClass('disabled');
                $('#left-button').addClass('disabled');
            } else {
                $('#left-button').addClass('disabled');
                $('#right-button').addClass('disabled');
                $('#right-ellipses').hide()
                $('#left-ellipses').hide()
            }
        }

    }).resize();

}

SetupFilterScrolling()

$(function () {

    /* Functions */

    var loadFilterForm = function () {
        var btn = $(this);
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                // Reset/Hide browser
                ResetHideBrowser()

                if ($(btn).hasClass('filter-preset-item')) {
                    $("#lightbox .filter-preset-item").removeClass("active blue");
                    $("#lightbox .filter-preset-item.option > i").removeClass("check").addClass('outline');
                    $(btn).addClass('active blue')
                    $('> i', btn).addClass('check').removeClass('outline')
                } else {
                    // Prevent mod_filter button from being selected.
                    $(btn).removeClass("selectable");

                    // remove popup
                    $("#mod_filter").popup('destroy')

                    // Disable all elements in variant tab utility bar
                    $('#variants-tab #tab-utility-bar').find('*').addClass('disabled')

                    // Hide lightbox, replace its content with modal and then display it.
                    $('#lightbox').dimmer('hide');
                }

            },
            success: function (data) {
                if ($(btn).hasClass('filter-preset-item')) {
                    $('#lightbox #filter-instance-container').html($(data.html_form).find('#filter-instance-container').html())
                    $('#lightbox #status-message').html($(data.html_form).find('#status-message').html())
                } else {
                    // Populate lightbox with modal featuring form.
                    $('#lightbox').html(data.html_form);

                    // Store the currently active stv as an attribute of the filter submit button.
                    // This allows it to be set to active once again when variant lists are refreshed.
                    var active_stv = $("#variant-menu .mini-tabs-link.active").attr('data-id')
                    $('#lightbox .js-modify-filter-form-submit').attr('data-stv', active_stv)

                    // Show lightbox
                    $('#lightbox').dimmer({
                        closable: false
                    }).dimmer('show');
                }
                SetupFiltersForm()
            }
        });
    };

    var saveFilterForm = function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            beforeSend: function () {
                // Load a loading circle if taking more than 3ms
                ajaxLoadTimeout = setTimeout(function () {
                    $("#variant-list-content-loader").addClass('active');
                }, 500);
            },
            success: function (data) {
                if (data.form_is_valid) {
                    $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                    $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())
                    $('#variants-tab #tab-utility-bar .filters-sub-menu-container').html(data.active_filters)

                    clearTimeout(ajaxLoadTimeout);
                    $("#variant-list-content-loader").removeClass('active');

                    // Apply searches to carry them over.
                    apply_variant_search()

                    $("#mod_filter").addClass("selectable");
                    // Enable all elements in variant tab utility bar
                    $('#variants-tab #tab-utility-bar').find('*').removeClass('disabled')

                    // Set the variant item that was active before filter was changed to being active
                    // again now that the variant lists have been refreshed.
                    stv = $('#lightbox .js-modify-filter-form-submit').attr('data-stv')
                    $('#variant-menu').find(`[data-id='${stv}']`).addClass('active blue')

                    if (!$("#variant-menu .mini-tabs-link.active")[0]) {
                        // If no active item variant is now not available as choice.
                        // Close variant details as it has been filtered out
                        $('.mini-tabs-link').removeClass('active blue');
                        $(".mini-tabs-content").hide();
                        $("#variant-content-loader").removeClass('active');
                        $(".basic_message").show();
                    }

                    // If no variants match filter, show notice message.
                    if (!$("#variant-menu #unpinned-list .gene").is(':visible')) {
                        $("#variant-menu #no-results-notice").removeClass('hidden')
                    } else { // otherwise hide notice
                        $("#variant-menu #no-results-notice").addClass('hidden')
                    }

                    // Refresh popups
                    $("#variant-menu .js-update-transcript,.pinned-transcript-popup, #mod_filter.selectable").popup({
                        inline: false
                    })

                    // Hide lightbox
                    $('#lightbox').dimmer('hide');

                    SetupFilterScrolling()
                }
                else {
                    $('#lightbox').html(data.html_form);
                    SetupFiltersForm()
                }
            }
        });
        return false;
    };


    /* Binding */

    // Modify Filter
    $("#variants-tab").on("click", '#mod_filter.selectable', loadFilterForm);
    $("#lightbox").on("click", '.filter-preset-item', loadFilterForm);
    $("#lightbox").on("submit", "#js-modify-filter-form", saveFilterForm);

});

// Filter formset functionality
function SetupFiltersForm() {
    // Initiate dropdowns in form.
    $('.filter-dropdown')
        .dropdown({
            direction: 'upward'
        });

    // Set all visible value fields to required. 
    $('#form-set [id*=value]').prop('required', true)


    // If click add button....
    $('#add_more').click(function () {
        // Retrieve current total number of forms.
        var form_idx = $('#id_items-TOTAL_FORMS').val();
        // Copy the empty form and paste it to end of form set. Replace __prefix__ with correct index.
        $('#match-field').before($('#empty-form').html().replace(/__prefix__/g, form_idx));
        // Add one to total forms.
        $('#id_items-TOTAL_FORMS').val(parseInt(form_idx) + 1);

        // Reinitiate all dropdowns for new row.
        $('.filter-dropdown')
            .dropdown({
                direction: 'upward'
            })
            ;

        // Define activity for new delete button
        $('.remove-formset-button').click(function () {
            delete_form(this)
        });

        // Ensure all visible value field are required.
        $('#form-set [id*=value]').prop('required', true)

        // Ensure formset is visible and classed correctly.
        $('#form-set').show()
        $('.add-container').addClass('bottom attached')
        control_match_field_visibility()
    });

    // Define activity for delete button
    $('.remove-formset-button').click(function () {
        delete_form(this)
    });

    // If click delete...
    function delete_form(button) {
        // Find the hidden delete checkbox nearby and check it. (Checkbox placed automatically by django and identifies it should be deleted).
        $(button).siblings('[id*=DELETE]').prop('checked', true)
        // Remove requirment for deleted form to have a value.
        $(button).siblings().find('[id*=value]').prop('required', false)
        // Hide the form row.
        $(button).parents('.form-row').hide()

        // If there are no visible form rows left, hide its container.
        $('#form-set').toggle($('.form-row:visible').length != 0);
        $('.add-container').toggleClass('bottom attached', $('.form-row:visible').length != 0);
        control_match_field_visibility()
    }

    function control_match_field_visibility() {
        if ($('.form-row:visible').length > 1) {
            $('#match-field').removeClass('hidden')
        } else {
            $('#match-field').addClass('hidden')
        }
    }

    // If there is no visble form rows, hide its container. Othwerwise show.
    $('#form-set').toggle($('.form-row:visible').length != 0);
    $('.add-container').toggleClass('bottom attached', $('.form-row:visible').length != 0);
    control_match_field_visibility()
}


// Click close button inside lightbox modal.
$("#lightbox").on("click", ".filter-settings-close", function () {
    // Reset look of filter button and filter bar

    $("#mod_filter").addClass("selectable");
    $("#variant-menu .js-update-transcript,.pinned-transcript-popup, #mod_filter.selectable").popup({
        inline: false
    })

    // Enable all elements in variant tab utility bar
    $('#variants-tab #tab-utility-bar').find('*').removeClass('disabled')

    // Hide lightbox
    $('#lightbox').dimmer('hide');
});

// ============
// PIN VARIANTS
// ============

function SetupVariantPinning() {
    $('.mini-tabs-content #pin-variant-checkbox').checkbox({ // If select toggle
        onChange: function () {
            // check if toggle is checked
            var ischecked = $('.mini-tabs-content #pin-variant-checkbox').checkbox('is checked')

            // toggle class of variant title to indicate selection status.
            $('.mini-tabs-content #variant-title').toggleClass('ischecked')
            $('.mini-tabs-content #variant-title #pinned-icon').toggleClass('hidden')

            // Update tooltip
            if (ischecked) {
                $('.mini-tabs-content #pin-variant-checkbox').attr("data-tooltip", "Unpin Variant");
            } else {
                $('.mini-tabs-content #pin-variant-checkbox').attr("data-tooltip", "Pin Variant");
            }

            // Initiate AJAX
            $.ajax(
                {
                    type: 'POST',
                    url: $('.mini-tabs-content #pin-variant-checkbox').attr('data-url'), //get url from toggle attribute
                    data: {
                        "ischecked": ischecked,
                        "csrfmiddlewaretoken": $('.mini-tabs-content #pin-variant-checkbox').attr('data-csrf') //send check status as data
                    },
                    beforeSend: function () {
                        // Load a loading circle if taking more than 3ms
                        ajaxLoadTimeout = setTimeout(function () {
                            $("#variant-list-content-loader").addClass('active');
                        }, 500);
                    },
                    success: function (data) {

                        // Use returned data to update the unpinned and pinned lists of variants. 
                        // This is done individually to retain search term and scroll positions.
                        $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                        $('#variant-menu #pinned-container').html($(data.variant_list).filter('#pinned-container').html())
                        $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())

                        clearTimeout(ajaxLoadTimeout);
                        $("#variant-list-content-loader").removeClass('active');

                        // Apply searches to carry them over.
                        apply_variant_search()

                        // Look at the stv id attribute from toggle and find the matching variant menu item and set its class to active.
                        // This will ensure that the menu item still appears selected once the variant lists have been updated.
                        stv = $('.mini-tabs-content #pin-variant-checkbox').attr('data-stv')
                        $('#variant-menu').find(`[data-id='${stv}']`).addClass('active blue')

                        // If there is an active menu item (variant still available as a choice)
                        if ($("#variant-menu .mini-tabs-link.active")[0]) {
                            // Scroll relevent list to active item
                            if (ischecked) {
                                $("#variant-menu #pinned-list").animate({
                                    scrollTop: $("#variant-menu #pinned-list").scrollTop() + $("#variant-menu .mini-tabs-link.active").position().top
                                        - $("#variant-menu #pinned-list").height() / 2 + $("#variant-menu .mini-tabs-link.active").height() / 2
                                }, 200);
                            } else {
                                setTimeout(function () {
                                    $("#variant-menu #unpinned-list").animate({
                                        scrollTop: $("#variant-menu #unpinned-list").scrollTop() + $("#variant-menu .mini-tabs-link.active").position().top
                                            - $("#variant-menu #unpinned-list").height() / 2 + $("#variant-menu .mini-tabs-link.active").height() / 2
                                    }, 200);
                                }, 100);

                            }
                        } else {
                            // If no active item variant is now not available as choice.
                            // Close variant details
                            $('.mini-tabs-link').removeClass('active blue');
                            $(".mini-tabs-content").hide();
                            $("#variant-content-loader").removeClass('active');
                            $(".basic_message").show();
                        }

                        // Refresh popups
                        $("#variant-menu .js-update-transcript,.pinned-transcript-popup").popup({
                            inline: false
                        })

                    },
                    error: function () {
                        alert("error");
                    }
                })
        }
    })
}

// ========================
// PREVIOUS CLASSIFICATIONS 
// ========================

function SetupClassificationsTable() {

    // Initiate sample table
    $('.mini-tabs-content .previous-classification-table').DataTable({
        'serverSide': false,
        'ajax': '/api/' + $('.mini-tabs-content .previous-classification-table').attr('data-stv') + '/previous_classifications_list?format=datatables',
        "deferRender": true,
        'processing': true,
        'columns': [
            { 'data': 'ss_samples.0.first_name', 'name': 'sample_variant__sample__patient__first_name' },
            { 'data': 'ss_samples.0.last_name', 'name': 'sample_variant__sample__patient__last_name' },
            {
                "data": null,
                "render": function (data, type, row, meta) {
                    data = $.map(row.ss_samples, function (ss_sample) {
                        return ss_sample.sample_identifier;
                    })
                    return data.join(', ');
                }
            },
            { 'data': 'ss_samples.0.lab_no', 'name': 'sample_variant__sample__lab_no' },
            {
                "data": null,
                "render": function (data, type, row, meta) {
                    data = $.map(row.ss_samples, function (ss_sample) {
                        return $.map(ss_sample.runs, function (runs) {
                            return runs.worksheet;
                        })
                    })
                    return data.filter((item, i, ar) => ar.indexOf(item) === i).join(', ');
                }
            },
            {
                "data": null,
                "render": function (data, type, row, meta) {
                    data = $.map(row.ss_samples, function (ss_sample) {
                        return $.map(ss_sample.runs, function (runs) {
                            return runs.pipeline_name;
                        })
                    })
                    return data.filter((item, i, ar) => ar.indexOf(item) === i).join(', ');
                }
            },
            { 'data': 'date_classified', 'searchable': false, "sortable": false },
            {
                "data": null,
                "render": function (data, type, row, meta) {
                    comment = row.comment
                    if (comment) {
                        data = '<i class="check circle icon"></i>'
                    } else {
                        data = '<i class="times circle icon"></i>'
                    }
                    return data;
                },
                "orderable": false,
                "className": 'left aligned',
            },
            { 'data': 'evidence_file_count', 'name': 'evidence_files__description' },
            { 'data': 'classification', 'name': 'comments__classification' },
        ],
        createdRow: function (row, data, index) {
            classification = data.classification
            if (classification === 'Benign') {
                $(row).addClass('left marked green');
            } else if (classification === 'Pathogenic') {
                $(row).addClass('left marked red');
            }
        },
        "ordering": false,
        "scrollCollapse": true,
        "paging": false,
        "pageLength": 25,
        "footer": false,
        "dom": '<"top">rt<"bottom"><"clear">',
        "language": {
            "emptyTable": "No previous classifications",
            'loadingRecords': '&nbsp;',
            'processing': 'Loading...',
            "zeroRecords": "No classifications matching query",
        },
        "order": [[3, 'desc']]

    });

    $(function () {
        $('.mini-tabs-content .previous-classification-table tbody').on('click', 'tr', function (event) {
            var row = $('.mini-tabs-content .previous-classification-table').DataTable().row(this);

            var previous_stv = row.data().id
            var current_stv = $('.mini-tabs-content .previous-classification-table').attr('data-stv')
            $.ajax({
                url: '/ajax/load_previous_evidence/' + current_stv + '/' + previous_stv,
                type: 'get',
                dataType: 'json',
                beforeSend: function () {
                    $('#lightbox')
                        .dimmer('hide')
                        ;
                },
                success: function (data) {
                    $("#lightbox").html(data.html_form);

                    $('#lightbox')
                        .dimmer('show')
                        ;

                    $('#lightbox .previous-evidence-close').click(function () {
                        $('#lightbox')
                            .dimmer('hide')
                            ;
                    })
                }
            });
        })


        $("#lightbox").on("submit", ".copy-evidence-form", function () {
            var form = $(this);
            $.ajax({
                url: form.attr("action"),
                data: form.serialize(),
                type: form.attr("method"),
                dataType: 'json',
                success: function (data) {
                    if (data.is_valid) {
                        $(".mini-tabs-content #evidence-container").html(data.documents)
                        $('.mini-tabs-content #readonly-comment-form').html(data.html_comment_display)
                        // Fade out existing classifcation, replace with new data from ajax data and fade back in. 
                        $('.mini-tabs-content #variant-classification-container').fadeOut(function () {
                            $('.mini-tabs-content #variant-classification-container').html(data.html_classification);
                            $('.mini-tabs-content #variant-classification-container').fadeIn(function () {
                                // Refresh variant classification popup
                                $(".mini-tabs-content .variant-classification").popup({
                                    inline: false,
                                    hoverable: true
                                })
                            });
                        })

                        // Ensure comment form is closed
                        $('.mini-tabs-content .js-update-create-comment-active-header').hide()
                        $('.mini-tabs-content .js-update-create-comment').show()
                        $('.mini-tabs-content #comment-form').hide()
                        $('.mini-tabs-content #readonly-comment-form').show()

                        $('#lightbox').dimmer("hide");
                        $('.mini-tabs-content .details-tabs .item')
                            .tab("change tab", 'evidence');
                    } else {
                        $("#lightbox").html(data.html_form);
                    }
                }
            });
            return false;
        });

    });

}



// ====================
// LOAD VARIANT DETAILS 
// ==================== 

$(document).ready(function () {

    $("#variant-menu").on("click", ".mini-tabs-link", function () {

        var tab_url = $(this).attr('data-url');

        // Load variant details from link and format it for jbrowse
        var chr = $(this).attr('data-chr');
        var location = $(this).attr('data-location');
        var left = +location - 5;
        var right = +location + 4;
        var coords = chr + ":" + left + '..' + right;

        if ($(this).hasClass('active')) {
            $('.mini-tabs-link').removeClass('active blue');
            $(".mini-tabs-content").hide();
            $("#variant-content-loader").removeClass('active');
            $(".basic_message").show();
        } else {
            $('.mini-tabs-link').removeClass('active blue');
            $(this).addClass('active blue');

            $(".basic_message").hide();

            $.ajax({
                url: tab_url,
                type: 'get',
                dataType: 'json',
                beforeSend: function () {
                    // Load a loading circle if taking more than 3ms
                    ajaxLoadTimeout = setTimeout(function () {
                        $("#variant-content-loader").addClass('active');
                    }, 300);
                },
                success: function (data) {
                    $(".mini-tabs-content").html(data.variant_details);
                    $(".mini-tabs-content").show();
                    $("#variant-content-container").scrollTop(0)

                    clearTimeout(ajaxLoadTimeout);
                    $("#variant-content-loader").removeClass('active');

                    // If browser is open, navigate to variant.
                    if ($('#browser').css("display") != 'none') {
                        const assemblyName = genomeView.state.assemblyManager.assemblies[0].name
                        genomeView.view.navToLocString(coords, assemblyName);
                    }

                    // Generate variant classification popup
                    $(".mini-tabs-content .variant-classification").popup({
                        inline: false,
                        hoverable: true
                    })

                    // Setup listener on pin toggle.
                    SetupVariantPinning()

                    // Setup table
                    SetupClassificationsTable()

                }
            });
        }
    })

})

// Hide non-active tabs initially
$('.mini-tabs-content').hide()

$("#variant-menu").on("click", "#menu-toggle-open", function () {
    $('#variant-menu').hide()
    $('.menu-toggle-closed').show()
})

$('.menu-toggle-closed').click(function () {
    $('#variant-menu').show()
    $('.menu-toggle-closed').hide()
})

// ===================
// VARIANT LIST SEARCH 
// ===================

// Create case insensitive .contains filter https://stackoverflow.com/questions/8746882/jquery-contains-selector-uppercase-and-lower-case-issue
jQuery.expr[':'].icontains = function (a, i, m) {
    return jQuery(a).text().toUpperCase()
        .indexOf(m[3].toUpperCase()) >= 0;
};

function apply_variant_search() {
    var query = $("#variant-menu #variant-search").val()
    // $("#variant-menu #unpinned-list .gene")
    //     .hide()
    //     .filter(':icontains("' + query + '")')
    //     .show();

    $("#variant-menu #unpinned-list .gene").show()
    $("#variant-menu #unpinned-list .mini-tabs-link").removeClass('hidden');
    if ($('#variant-menu #unpinned-list .gene .title').is(':icontains("' + query + '")')) {
        $("#variant-menu #unpinned-list .gene")
            .hide()
            .filter(':icontains("' + query + '")')
            .show();
    } else {
        $("#variant-menu #unpinned-list .mini-tabs-link")
            .addClass('hidden')
            .filter(':icontains("' + query + '")')
            .removeClass('hidden');

        $('#variant-menu #unpinned-list .gene').each(function () {
            if ($(this).find('.mini-tabs-link:visible').length == 0) {
                $(this).hide();
            }
        });
    }

    // If no variants match query, show notice message.
    if (!$("#variant-menu #unpinned-list .gene").is(':visible')) {
        $("#variant-menu #no-results-notice").removeClass('hidden')
    } else { // otherwise hide notice
        $("#variant-menu #no-results-notice").addClass('hidden')
    }

    // Update header message
    if (query) {
        $("#variant-menu .variant-sub-menu-header.unpinned i").removeClass('tasks').addClass('search')
        $("#variant-menu .variant-sub-menu-header.unpinned .title").text("SEARCHING FOR: '" + query + "'")
    } else {
        $("#variant-menu .variant-sub-menu-header.unpinned i").addClass('tasks').removeClass('search')
        $("#variant-menu .variant-sub-menu-header.unpinned .title").text('ALL VARIANTS')
    }
}

$("#variant-menu").on("keyup search", "#variant-search", apply_variant_search);


// ==========================
// UPDATE SELECTED TRANSCRIPT 
// ==========================

// Initialise pop-ups
$("#variant-menu .js-update-transcript,.pinned-transcript-popup, #mod_filter.selectable").popup({
    inline: false
})

$(function () {

    /* Functions */

    var loadTranscriptForm = function () {
        var btn = $(this);
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                ResetHideBrowser()
                $('#lightbox').dimmer('hide');
            },
            success: function (data) {

                // Disable all elements in variant tab utility bar
                $('#variants-tab #tab-utility-bar').find('*').addClass('disabled')

                // Populate lightbox with modal featuring form.
                $('#lightbox').html(data.html_form);

                // Filter table of variants to show only those relevent to the current transcript
                currently_selected_transcript = $("#lightbox .selected-transcript").attr('data-current');
                $("#lightbox .variant-row").hide().filter('[data-transcript-id="' + currently_selected_transcript + '"]').show()

                // Show lightbox
                $('#lightbox').dimmer({
                    closable: false
                }).dimmer('show');
            }
        });
    };

    var saveTranscriptForm = function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            beforeSend: function () {
                // Load a loading circle if taking more than 5ms
                ajaxLoadTimeout = setTimeout(function () {
                    $("#variant-list-content-loader").addClass('active');
                }, 500);
            },
            success: function (data) {
                if (data.form_is_valid) {
                    $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                    $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())

                    clearTimeout(ajaxLoadTimeout);
                    $("#variant-list-content-loader").removeClass('active');

                    // Hide lightbox
                    $('#lightbox').dimmer('hide');

                    // Enable tab utility bar
                    $('#variants-tab #tab-utility-bar').find('*').removeClass('disabled')

                    // Close any open variants
                    $('.mini-tabs-link').removeClass('active blue');
                    $(".mini-tabs-content").hide();
                    $("#variant-content-loader").removeClass('active');
                    $(".basic_message").show();

                    // Apply any search carried over from before transcript change.
                    apply_variant_search()

                    // Refresh popups
                    $("#variant-menu .js-update-transcript,.pinned-transcript-popup").popup({
                        inline: false
                    })
                }
                else {
                    $('#lightbox').html(data.html_form);
                }
            }
        });
        return false;
    };


    /* Binding */

    // Update transcript
    $("#variant-menu").on("click", ".js-update-transcript", loadTranscriptForm);
    $("#lightbox").on("submit", "#js-update-transcript-form", saveTranscriptForm);

});

// When select a different transcript
$("#lightbox").on("click", ".transcript-choice", function () {
    // Deselect others and make this appear selected
    $("#lightbox .transcript-choice").removeClass('selected').addClass('deselected link')
    $(this).addClass('selected').removeClass('deselected link')

    // Extract new and previous transcript id's from data attributes.
    var new_transcript = $(this).attr('data-transcript-id');
    var currently_selected_transcript = $("#lightbox .selected-transcript").attr('data-current');

    // Set hidden input value to new transcript. This will be sent to server when user submits form.
    $("#lightbox .selected-transcript").val(new_transcript);

    // Check whether user has chosen a different transcript, if so allow them to save changes.
    if (new_transcript === currently_selected_transcript) {
        $("#lightbox .js-update-transcript-form-submit").addClass('disabled')
    } else {
        $("#lightbox .js-update-transcript-form-submit").removeClass('disabled')
    }

    // Filter table of variants to show only those relevent to the new transcript
    $("#lightbox .variant-row").hide().filter('[data-transcript-id="' + new_transcript + '"]').show()
});

// ===============
// VARIANT COMMENT 
// =============== 

$(function () {

    /* Functions */

    var loadCommentForm = function () {
        var btn = $(this);
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $('.mini-tabs-content .js-update-create-comment').hide()
                $('.mini-tabs-content .js-update-create-comment-active-header').show()
            },
            success: function (data) {
                $('.mini-tabs-content #readonly-comment-form').hide()
                $('.mini-tabs-content #comment-form').fadeIn()
                $('.mini-tabs-content #comment-form').html(data.html_form);
                $('.ui.dropdown').dropdown();
            }
        });
    };

    var saveCommentForm = function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.form_is_valid) {
                    $('.mini-tabs-content #readonly-comment-form').html(data.html_comment_display)

                    $('.mini-tabs-content .js-update-create-comment-active-header').hide()
                    $('.mini-tabs-content .js-update-create-comment').show()

                    $('.mini-tabs-content #comment-form').hide()
                    $('.mini-tabs-content #readonly-comment-form').fadeIn()

                    // Fade out existing classifcation, replace with new data from ajax data and fade back in. 
                    $('.mini-tabs-content #variant-classification-container').fadeOut(function () {
                        $('.mini-tabs-content #variant-classification-container').html(data.html_classification);
                        $('.mini-tabs-content #variant-classification-container').fadeIn(function () {
                            // Refresh variant classification popup
                            $(".mini-tabs-content .variant-classification").popup({
                                inline: false,
                                hoverable: true
                            })
                        });
                    })
                }
                else {
                    $('.mini-tabs-content #comment-form').html(data.html_form);
                }
            }
        });
        return false;
    };


    /* Binding */

    // Update transcript
    $(".mini-tabs-content").on("click", ".js-update-create-comment", loadCommentForm);
    $(".mini-tabs-content").on("submit", "#js-comment-update-create-form", saveCommentForm);

});

// Create cancel button to close comment form.
$(".mini-tabs-content").on("click", ".js-comment-update-create-cancel", function () {
    $('.mini-tabs-content .js-update-create-comment-active-header').hide()
    $('.mini-tabs-content .js-update-create-comment').show()
    $('.mini-tabs-content #comment-form').hide()
    $('.mini-tabs-content #readonly-comment-form').fadeIn()
});

// Create shortcut button to alter pathogenicity classification.
$(".mini-tabs-content").on("click", ".update-classification-button", function () {
    $('.mini-tabs-content .variant-classification').popup('hide')
    $('.mini-tabs-content .details-tabs .item')
        .tab("change tab", 'evidence')
        ;
    $('.mini-tabs-content .js-update-create-comment').trigger('click');
});

$(".mini-tabs-content").on("click", "#comment-history", function () {
    $('#lightbox').dimmer('hide');
    $('#lightbox').html($(".mini-tabs-content #comment-history-container").html())
    $('#lightbox').dimmer({
        closable: false
    }).dimmer('show');

    $('.fake-textarea').each(function (i, obj) {
        var dmp = new diff_match_patch();
        var text1 = $(this).attr('data-value-previous').trim()
        var text2 = $(this).text().trim()
        var d = dmp.diff_main(text1, text2);
        dmp.diff_cleanupSemantic(d);
        var ds = dmp.diff_prettyHtml(d);
        $(this).html(ds)
    });
});

// ===============
// DELETE EVIDENCE 
// =============== 

$(function () {

    /* Functions */

    var loadArchiveEvidenceForm = function () {
        var btn = $(this);
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $('#lightbox').dimmer('hide');
            },
            success: function (data) {
                // Populate lightbox with modal featuring form.
                $('#lightbox').html(data.html_form);

                // Show lightbox
                $('#lightbox').dimmer({
                    closable: false
                }).dimmer('show');
            }
        });
    };

    var confirmArchiveEvidenceForm = function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.is_valid) {
                    $(".mini-tabs-content #evidence-container").html(data.documents)
                    $('#lightbox').dimmer('hide');

                }
                else {
                    $('.mini-tabs-content #comment-form').html(data.html_form);
                }
            }
        });
        return false;
    };


    /* Binding */

    // Update transcript
    $(".mini-tabs-content").on("click", ".archive-evidence", loadArchiveEvidenceForm);
    $("#lightbox").on("submit", "#archive-evidence-form", confirmArchiveEvidenceForm);
    $("#lightbox").on("click", ".archive-evidence-close", function () {
        // Hide lightbox
        $('#lightbox').dimmer('hide');
    });

});


// =======================
// GENOME BROWSER CONTROLS 
// ======================= 

$('#browser,#browser-expand-collapse').hide()


$('.view-in-browser').click(function () {
    $('#variants-main-panel').show();
    $("#browser-expand-collapse").removeClass("primary")
    $('#browser-expand-collapse .icon').addClass("expand").removeClass("compress")
    $('#browser').addClass("browser-collapsed").removeClass("browser-expanded");

    if ($('#browser').css("display") === 'none') {
        $(this).attr("data-tooltip", "Hide Browser");
    } else {
        $(this).attr("data-tooltip", "Show Browser");
    }

    $('#browser').toggle();
    $('#browser-expand-collapse').toggle()
    $(this).toggleClass("red");

    // Trigger resize to force jbrowse to update width.
    window.dispatchEvent(new Event('resize'));

    // Reset position of browser to that of active variant. 
    var chr = $('.mini-tabs-link.active').attr('data-chr');
    var location = $('.mini-tabs-link.active').attr('data-location');
    var left = +location - 5;
    var right = +location + 4;
    var coords = chr + ":" + left + '..' + right;

    // Delay by 1s to ensure browser is loaded first.
    const assemblyName = genomeView.state.assemblyManager.assemblies[0].name
    setTimeout(function () { genomeView.view.navToLocString(coords, assemblyName); }, 1000);

})

$('#browser-expand-collapse').click(function () {
    $('#variants-main-panel').toggle();

    if ($('#browser').hasClass('browser-collapsed')) {
        $(this).attr("data-tooltip", "Collapse Browser");
    } else {
        $(this).attr("data-tooltip", "Expand Browser");
    }

    $('#browser').toggleClass("browser-collapsed").toggleClass("browser-expanded");
    $('#browser-expand-collapse .icon').toggleClass("expand").toggleClass("compress")
    $(this).toggleClass("primary")
})

// ============
// COVERAGE TAB 
// ============ 

$(document).ready(function () {

    function ColourCells(td, cellData) {
        if (cellData > 95) {
            $(td).addClass('positive');
        } else if (cellData > 80) {
            $(td).addClass('warning');
        } else {
            $(td).addClass('negative');
        }
    }

    var gene_table = $('#gene-table').DataTable({
        'serverSide': false,
        'ajax': '/api/' + $('#gene-table').attr('data-run') + '/' + $('#gene-table').attr('data-ss_sample') + '/gene_report_list?format=datatables',
        "deferRender": true,
        'processing': true,
        'columns': [
            { 'data': 'gene_name', 'name': 'gene__hgnc_name' },
            { 'data': 'coverage_info.cov_10x' },
            { 'data': 'coverage_info.cov_20x' },
            { 'data': 'coverage_info.cov_30x' },
            { 'data': 'coverage_info.cov_40x' },
            { 'data': 'coverage_info.cov_50x' },
            { 'data': 'coverage_info.cov_100x' },
            { 'data': 'coverage_info.cov_min' },
            { 'data': 'coverage_info.cov_max' },
            {
                'data': 'coverage_info.cov_mean',
                'render': function (data, type, full) {
                    return parseFloat(data).toFixed(0);
                }
            },
            {
                'data': 'coverage_info.pct_10x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_20x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_30x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_40x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_50x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_100x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
        ],
        "scrollCollapse": true,
        "ordering": true,
        "scrollCollapse": true,
        "paging": false,
        "pageLength": 25,
        "footer": false,
        "dom": '<"top">rt<"bottom"><"clear">',
        "language": {
            "emptyTable": "No gene coverage data",
            'loadingRecords': '&nbsp;',
            'processing': 'Loading...',
            "zeroRecords": "No genes matching query",
        },
        "order": [[0, 'asc']]
    });


    var exon_table = $('#exon-table').DataTable({
        'serverSide': false,
        'ajax': '/api/' + $('#exon-table').attr('data-run') + '/' + $('#gene-table').attr('data-ss_sample') + '/exon_report_list?format=datatables',
        "deferRender": true,
        'processing': true,
        'columns': [
            { 'data': 'gene_name', 'name': 'exon__transcript__gene__hgnc_name' },
            { 'data': 'exon_number', 'name': 'exon__number' },
            { 'data': 'coverage_info.cov_10x' },
            { 'data': 'coverage_info.cov_20x' },
            { 'data': 'coverage_info.cov_30x' },
            { 'data': 'coverage_info.cov_40x' },
            { 'data': 'coverage_info.cov_50x' },
            { 'data': 'coverage_info.cov_100x' },
            { 'data': 'coverage_info.cov_min' },
            { 'data': 'coverage_info.cov_max' },
            {
                'data': 'coverage_info.cov_mean',
                'render': function (data, type, full) {
                    return parseFloat(data).toFixed(0);
                }
            },
            {
                'data': 'coverage_info.pct_10x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_20x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_30x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_40x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_50x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
            {
                'data': 'coverage_info.pct_100x',
                createdCell: function (td, cellData, rowData, row, col) {
                    ColourCells(td, cellData)
                }
            },
        ],
        "scrollCollapse": true,
        "ordering": true,
        "scrollCollapse": true,
        "paging": false,
        "pageLength": 25,
        "footer": false,
        "dom": '<"top">rt<"bottom"><"clear">',
        "language": {
            "emptyTable": "No gene coverage data",
            'loadingRecords': '&nbsp;',
            'processing': 'Loading...',
            "zeroRecords": "No genes matching query",
        },
        "order": [[0, 'asc']]
    });

    // Toggle visibility of raw values columns
    $('#columns-toggle').on('click', function () {
        $(this).toggleClass('red')

        if (!gene_table.column(2).visible()) {
            $(this).attr("data-tooltip", "Hide Raw Depth Values");
        } else {
            $(this).attr("data-tooltip", "Show Raw Depth Values");
        }

        gene_table.columns('.toggle-cols').visible(!gene_table.column(2).visible());
        exon_table.columns('.toggle-cols').visible(!exon_table.column(2).visible());

    });

    // Set up custom search of both tables
    $('#mySearch').on('keyup click search', function () {
        $('#gene-table tbody tr').children('td').removeClass('row-selected')
        gene_table.search($(this).val()).draw();
        exon_table.search($(this).val()).draw();
    });

    // Hide raw value columns by default
    gene_table.columns('.toggle-cols').visible(false)
    exon_table.columns('.toggle-cols').visible(false)

    // Set up toggle button for min-depth-filter
    $('#min-read-filter-toggle').on('click', function () {
        $(this).toggleClass('red')

        if ($('#min-read-filter-input').css("display") === 'none') {
            $('#max-value').val('100')
            $(this).attr("data-tooltip", "Remove Depth Filter");
        } else {
            $('#max-value').val('')
            $(this).attr("data-tooltip", "Activate Depth Filter");
        }

        $('#min-read-filter-input').toggle()
        gene_table.draw();
        exon_table.draw();
    })

    // Update tables when filter value modified
    $('#max-value').on('keyup click', function () {
        gene_table.draw();
        exon_table.draw();
    });


    // Search exon table when select gene
    $('#gene-table tbody').on('click', 'tr', function (event) {
        var row = gene_table.row(this);
        var selected_gene = row.data().gene_name

        if ($(this).children('td').hasClass('row-selected')) {
            $(this).children('td').removeClass('row-selected')
            exon_table.search('').draw()
        } else {
            $('#gene-table tbody tr').children('td').removeClass('row-selected');
            $(this).children('td').addClass('row-selected');
            exon_table.search(selected_gene).draw();
        }
    });

});

$('#min-read-filter-input').hide()

$.fn.dataTable.ext.search.push(
    function (settings, data, dataIndex) {
        // Don't filter on anything other than "exon-table"
        if (settings.nTable.id !== 'exon-table') {
            return true;
        }

        // alert(data[6])
        var max = parseInt($('#max-value').val(), 10);
        var depth = parseFloat(data[8]) || 0; // use data for the age column

        if (isNaN(max) ||
            (depth <= max)) {
            return true;
        }
        return false;
    }
);

// ==========
// REPORT TAB
// ========== 


function SetupReportForm() {


    $('.results-cards .card').click(function () {
        if ($(event.target).hasClass("prevent-comment-display")) {
            null
        } else {
            $('#report #report-lightbox').html($('#report .report-info-container').html())

            $(this).addClass('info-active')
            var hgvs = $(this).attr('data-hgvs')
            var unpinned = $(this).attr('data-unpinned')
            var updated = $(this).attr('data-updated')
            var comment = $(this).attr('data-comment')
            var previous_comment = $(this).attr('data-previous-comment')
            var classification = $(this).attr('data-classification')
            var classification_colour = $(this).attr('data-classification-colour')
            var previous_classification = $(this).attr('data-previous-classification')
            var previous_classification_colour = $(this).attr('data-previous-classification-colour')

            $('#report #report-lightbox .title-text').text('Variant information: ' + hgvs)

            $('#report #report-lightbox .report-info-comment').html(comment)

            $('#report #report-lightbox .report-info-classification .text').text(classification)
            $('#report #report-lightbox .report-info-classification').addClass(classification_colour)

            if (updated == 'classification' || updated == 'both') {
                $('#report #report-lightbox .previous-classification-container').removeClass('hidden')
                $('#report #report-lightbox .previous.report-info-classification .text').text(previous_classification)
                $('#report #report-lightbox .previous.report-info-classification').addClass(previous_classification_colour)
            }

            if (updated == 'comment' || updated == 'both') {
                var dmp = new diff_match_patch();
                var text1 = previous_comment.trim()
                var text2 = comment.trim()
                var d = dmp.diff_main(text1, text2);
                dmp.diff_cleanupSemantic(d);
                var ds = dmp.diff_prettyHtml(d);
                $('#report #report-lightbox .report-info-comment').html(ds)
            }

            $('.existing-report,.new-report').addClass('existing-confirm-check disabled')
            $('#report #report-lightbox').dimmer({
                closable: false
            }).dimmer('show');
        }
    })


    $('.report-result-toggle').click(function () {
        var value = $(this).attr('data-id')
        // If item already checked
        if ($('i', this).hasClass('check')) {
            // Find the hidden input with the relevent value and remove it.
            $("input[name=selected-stvs][value='" + value + "']").remove();
            // Remove the check
            $('i', this).removeClass('check').addClass('outline')
            $(this).parents('.result-stv').removeClass('selected').addClass('deselected');
        } else {
            // If item not already checked
            // Create a hidden input with the relevent value
            $('<input>', {
                type: 'hidden',
                name: 'selected-stvs',
                value: value
            }).appendTo('#js-report-form');
            // Add check
            $('i', this).addClass('check').removeClass('outline')
            $(this).parents('.result-stv').removeClass('deselected').addClass('selected');
        }
    })
}


$(function () {

    /* Functions */

    var loadReportData = function () {
        var btn = $(this);

        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $('#report .report-dimmer').dimmer('show');
            },
            success: function (data) {
                // $('#report-container').html(data.report_container)
                if (data.show_new_button) {
                    $('.report-main-panel').hide()
                    $('.report-create-panel, .new-report').show()
                } else {
                    $('.report-create-panel').hide()
                    $('.report-main-panel').show()
                }
                $('#report #tab-utility-bar').html($(data.report_container).filter('#tab-utility-bar').html())
                $('#report #report-form-container').html($(data.report_container).find('#report-form-container').html())

                $('#report .report-pdf').attr('data', '/ajax/generate_report/?context=' + data.report_context_string)
                $('#report .report-pdf').attr('data-context', data.report_context_string)
                $('#report .report-dimmer').dimmer('hide');
                SetupReportForm()
            }
        });


    };

    var SaveReportData = function () {
        var form = $(this);
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            beforeSend: function () {
                $('#report .report-dimmer').dimmer('show');
            },
            success: function (data) {
                if (data.is_valid) {

                    // If info modal is active store the relevent stv id
                    if ($("#report .results-cards .card.info-active")[0]) {
                        var active_stv_id = $("#report .results-cards .card.info-active .report-result-toggle").attr('data-id')
                    }

                    if (data.refresh) {
                        $('#report #report-form-container .results-section').html($(data.report_container).find('#report-form-container .results-section').html())
                        $('#report #report-form-container .report-hidden-inputs').html($(data.report_container).find('#report-form-container .report-hidden-inputs').html())
                        $("input[name=refresh-results]").remove();
                    } else {
                        $('#report #tab-utility-bar').html($(data.report_container).filter('#tab-utility-bar').html())
                        $('#report #report-form-container').html($(data.report_container).find('#report-form-container').html())

                    }
                    $('#report .report-pdf').attr('data', '/ajax/generate_report/?context=' + data.report_context_string)
                    $('#report .report-pdf').attr('data-context', data.report_context_string)
                    $('#report .report-dimmer').dimmer('hide');
                    SetupReportForm()

                    // Find updated card with right id and simulate clicking on card to reload updated info.
                    $('#report .report-result-toggle[data-id="' + active_stv_id + '"]').parents('.card').addClass('info-active').trigger('click')
                }
            }
        });
        return false;
    };


    /* Binding */
    $('.main-tabs-link[data-tab="report"]').click(function () {
        if ($("#report .existing-report.active-instance")[0]) {
            $('<input>', {
                type: 'hidden',
                name: 'refresh-results',
                value: $('#report .report-pdf').attr('data-context')
            }).appendTo('#js-report-form');
            $("#report #js-report-form").submit();
        } else {
            $('.report-main-panel, .new-report').hide()
            $('.report-create-panel').show()
            loadReportData.call($(this))
        }
    })

    $("#report").on("click", ".new-report:not(.disabled)", function () {

        if ($("#report .existing-report.active-instance.modified-report")[0]) {

            $('#report #report-lightbox').html($('#report .report-confirm-discard-container').html())

            var active_report = $('#report .existing-report.active-instance').attr('data-name')
            text = "Are you sure you want to discard the changes made to '" + active_report + "' and create a new report?"
            $('#report #report-lightbox .title-text').text('Unsaved changes')
            $('#report #report-lightbox .content-text').text(text)
            $('#report #report-lightbox .report-confirm-discard-submit').addClass('open-report').attr('data-url', $(this).attr('data-url'))
            $(this).addClass('new-confirm-check disabled')
            $('.existing-report').addClass('new-confirm-check disabled')
            $('#report #report-lightbox').dimmer({
                closable: false
            }).dimmer('show');
        } else {
            $('.report-main-panel, .new-report').show()
            $('.report-create-panel').hide()
            loadReportData.call($(this))
        }

    });

    $("#report").on("click", ".existing-report:not(.active-instance,.disabled)", function () {
        if ($("#report .existing-report.active-instance.modified-report")[0] || $("#report .existing-report.active-instance.unsaved-report")[0]) {

            $('#report #report-lightbox').html($('#report .report-confirm-discard-container').html())

            var active_report = $('#report .existing-report.active-instance').attr('data-name')
            var new_report = $(this).attr('data-name')

            if ($("#report .existing-report.active-instance.unsaved-report")[0]) {
                text = "Are you sure you want to discard the unsaved report '" + active_report + "' and open '" + new_report + "'?"
                $('#report #report-lightbox .title-text').text('Unsaved report')
                $('.existing-report').addClass('existing-confirm-check disabled')
            } else {
                text = "Are you sure you want to discard the changes  made to  '" + active_report + "' and open '" + new_report + "'?"
                $('#report #report-lightbox .title-text').text('Unsaved changes')
                $('.existing-report,.new-report').addClass('existing-confirm-check disabled')
            }
            $('#report #report-lightbox .content-text').text(text)
            $('#report #report-lightbox .report-confirm-discard-submit').addClass('open-report').attr('data-url', $(this).attr('data-url'))
            $(this).addClass('grey')
            // Show lightbox
            $('#report #report-lightbox').dimmer({
                closable: false
            }).dimmer('show');
        } else {
            $('.report-main-panel, .new-report').show()
            $('.report-create-panel').hide()
            loadReportData.call($(this))
        }
    });


    $("#report").on("click", ".open-report", function () {
        $('#report #report-lightbox').dimmer('hide');
        loadReportData.call($(this))
    });


    $("#report").on("click", ".js-revert-form", loadReportData);
    $("#report").on("submit", "#js-report-form", SaveReportData);

    $("#report").on("click", ".js-save-report", function () {
        $("#report #js-report-form #commit-input").val('true')
        if ($("#report #js-report-form")[0].reportValidity()) {
            $("#report #js-report-form").submit();
        }

    });

    $("#report #report-lightbox").on("click", ".report-confirm-discard-close", function () {
        $('#report .new-confirm-check').removeClass('new-confirm-check disabled')
        $('#report .existing-confirm-check').removeClass('existing-confirm-check disabled')
        $('#report .existing-report').removeClass('grey')
        $('#report #report-lightbox').dimmer('hide');
        $('.results-cards .card').removeClass('info-active')
    });

});


// ==============
// GENOME BROWSER
// ============== 

var sample = $('#jbrowse_linear_view').attr('data-sample');
var vcf = $('#jbrowse_linear_view').attr('data-vcf');
var tbi = $('#jbrowse_linear_view').attr('data-tbi');
var bam = $('#jbrowse_linear_view').attr('data-bam');
var bai = $('#jbrowse_linear_view').attr('data-bai');
var media = $('#jbrowse_linear_view').attr('data-media-url');

const genomeView = new JBrowseLinearGenomeView({
    container: document.getElementById('jbrowse_linear_view'),
    assembly: {
        name: 'hg19',
        sequence: {
            type: 'ReferenceSequenceTrack',
            trackId: 'hg19',
            adapter: {
                type: 'BgzipFastaAdapter',
                fastaLocation: {
                    uri:
                        'https://jbrowse.org/genomes/hg19/fasta/hg19.fa.gz',
                },
                faiLocation: {
                    uri:
                        'https://jbrowse.org/genomes/hg19/fasta/hg19.fa.gz.fai',
                },
                gziLocation: {
                    uri:
                        'https://jbrowse.org/genomes/hg19/fasta/hg19.fa.gz.gzi',
                }
            },
        },
        "refNameAliases": {
            "adapter": {
                "type": "RefNameAliasAdapter",
                "location": {
                    "uri": "https://s3.amazonaws.com/jbrowse.org/genomes/hg19/hg19_aliases.txt"
                }
            }
        }
    },
    tracks: [
        {
            "type": 'FeatureTrack',
            "trackId":
                'ncbi_gff_hg19',
            "name": 'NCBI RefSeq (GFF3Tabix)',
            "category": ['Genes'],
            "assemblyNames": ['hg19'],
            "adapter": {
                "type": 'Gff3TabixAdapter',
                "gffGzLocation": {
                    "uri":
                        'https://s3.amazonaws.com/jbrowse.org/genomes/hg19/ncbi_refseq/GRCh37_latest_genomic.sort.gff.gz',
                },
                "index": {
                    "location": {
                        'uri':
                            'https://s3.amazonaws.com/jbrowse.org/genomes/hg19/ncbi_refseq/GRCh37_latest_genomic.sort.gff.gz.tbi',
                    },
                    "indexType": 'TBI',
                },
            },
            "renderer": {
                "type": 'SvgFeatureRenderer',
            },
        },
        {
            "type": "AlignmentsTrack",
            "trackId": "alignment_test",
            "name": bam,
            "assemblyNames": ["hg19"],
            "category": [sample, 'Alignments'],
            "adapter": {
                "type": "BamAdapter",
                "bamLocation": {
                    "uri": media + bam
                },
                "index": {
                    "location": {
                        "uri": media + bai
                    }
                }
            }
        },
        {
            "type": "VariantTrack",
            "trackId": "vcf_test",
            "name": vcf,
            "assemblyNames": ["hg19"],
            "category": [sample, 'Variants'],
            "adapter": {
                "type": "VcfTabixAdapter",
                "vcfGzLocation": { "uri": media + vcf },
                "index": { "location": { "uri": media + tbi } }
            }
        }],
    defaultSession: {
        name: 'this session',
        view: {
            "id": "linearGenomeView",
            "type": "LinearGenomeView",
            "offsetPx": 2087472352,
            "bpPerPx": 0.01,
            "displayName": 'VariantViewer - ' + sample,
            "displayedRegions": [],
            "tracks": [
                {
                    "id": "zoLe_b8_j",
                    "type": "ReferenceSequenceTrack",
                    "configuration": "hg19",
                    "displays": [
                        {
                            "id": "g4SyLlEDdI",
                            "type": "LinearReferenceSequenceDisplay",
                            "height": 44,
                            "configuration": "hg19-LinearReferenceSequenceDisplay",
                            "showForward": true,
                            "showReverse": true,
                            "showTranslation": false
                        }
                    ]
                },
                {
                    "id": "WzpyXHqsw",
                    "type": "AlignmentsTrack",
                    "configuration": "alignment_test",
                    "displays": [
                        {
                            "id": "EuLBW2f8ZB",
                            "type": "LinearAlignmentsDisplay",
                            "PileupDisplay": {
                                "id": "sKwcWEd3N0",
                                "type": "LinearPileupDisplay",
                                "height": 50,
                                "configuration": {
                                    "type": "LinearPileupDisplay",
                                    "displayId": "alignment_test-LinearAlignmentsDisplay_pileup_xyz",
                                    "renderers": {
                                        "PileupRenderer": {
                                            "type": "PileupRenderer"
                                        },
                                        "SvgFeatureRenderer": {
                                            "type": "SvgFeatureRenderer"
                                        }
                                    }
                                },
                                "showSoftClipping": false,
                                "filterBy": {
                                    "flagInclude": 0,
                                    "flagExclude": 1536
                                }
                            },
                            "SNPCoverageDisplay": {
                                "id": "Y_I4865YWS",
                                "type": "LinearSNPCoverageDisplay",
                                "height": 50,
                                "configuration": {
                                    "type": "LinearSNPCoverageDisplay",
                                    "displayId": "alignment_test-LinearAlignmentsDisplay_snpcoverage_xyz",
                                    "renderers": {
                                        "SNPCoverageRenderer": {
                                            "type": "SNPCoverageRenderer"
                                        }
                                    }
                                },
                                "selectedRendering": "",
                                "resolution": 1,
                                "constraints": {},
                                "filterBy": {
                                    "flagInclude": 0,
                                    "flagExclude": 1536
                                }
                            },
                            "configuration": "alignment_test-LinearAlignmentsDisplay",
                            "height": 140,
                            "showCoverage": true,
                            "showPileup": true
                        }
                    ]
                },
                {
                    "id": "WLv6XdMIC",
                    "type": "VariantTrack",
                    "configuration": "vcf_test",
                    "displays": [
                        {
                            "id": "t9iR3GMoJo",
                            "type": "LinearVariantDisplay",
                            "height": 62,
                            "configuration": "vcf_test-LinearVariantDisplay"
                        }
                    ]
                }
            ],
            "hideHeader": false,
            "hideHeaderOverview": false,
            "trackSelectorType": "hierarchical",
            "trackLabels": "overlapping",
            "showCenterLine": true
        },
    },
    location: ''
})