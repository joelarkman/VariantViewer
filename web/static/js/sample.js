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


// ==============
// VARIANT FILTER 
// ============== 

// Filters scroll
$(function () {

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
                $('#right-button').addClass('disabled');
                $('#left-button').removeClass('disabled');
            } else if ($(this).scrollLeft() === 0) { // when fully scrolled left
                $('#left-button').addClass('disabled');
                $('#right-button').removeClass('disabled');
            } else {
                $('#right-button').removeClass('disabled');
                $('#left-button').removeClass('disabled');
            }

            // For troubleshooting!
            // console.log($('#testing123').scrollLeft() + $('#testing123').innerWidth())
            // console.log($('#testing123')[0].scrollWidth)
        })
    });

    $(window).on('resize', function () {
        if ($('.active-filters-container')[0].offsetWidth < $('.active-filters-container')[0].scrollWidth) {
            $('#right-button').removeClass('disabled');
            $('#left-button').addClass('disabled');
        } else {
            $('#left-button').addClass('disabled');
            $('#right-button').addClass('disabled');
        }
    }).resize();

});

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
                    $("#lightbox .filter-preset-item > i").removeClass("check");
                    $(btn).addClass('active blue')
                    $('> i', btn).addClass('check')
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
            success: function (data) {
                if (data.form_is_valid) {
                    $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                    $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())
                    $('#variants-tab #tab-utility-bar .filters-sub-menu-container').html(data.active_filters)

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
                    type: 'get',
                    url: $('.mini-tabs-content #pin-variant-checkbox').attr('data-url'), //get url from toggle attribute
                    data: {
                        "ischecked": ischecked, //send check status as data
                    },
                    success: function (data) {

                        // Use returned data to update the unpinned and pinned lists of variants. 
                        // This is done individually to retain search term and scroll positions.
                        $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                        $('#variant-menu #pinned-container').html($(data.variant_list).filter('#pinned-container').html())
                        $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())

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

// $("#variant-menu").on("click", ".variant-sub-menu", function () {
//     // Reset look of filter button and filter bar
//     $("#variant-menu .variant-sub-menu").removeClass('active')
//     $(this).addClass('active')

//     if ($(this).hasClass('pinned')) {
//         $("#variant-menu #pinned-list").show()
//         $("#variant-menu #unpinned-list").hide()
//     } else {
//         $("#variant-menu #pinned-list").hide()
//         $("#variant-menu #unpinned-list").show()
//     }


// });

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
    $("#variant-menu #unpinned-list .gene")
        .hide()
        .filter(':icontains("' + query + '")')
        .show();

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
            success: function (data) {
                if (data.form_is_valid) {
                    $('#variant-menu #unpinned-list').html($(data.variant_list).filter('#unpinned-list').html())
                    $('#variant-menu #pinned-list').html($(data.variant_list).filter('#pinned-list').html())

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
    $("#lightbox .transcript-choice").removeClass('inverted')
    $("#lightbox .transcript-choice").addClass('link')
    $(this).addClass('inverted')
    $(this).removeClass('link')

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

    // Initiate coverage tables
    var cov_tables = $('.coverage-tables').DataTable({
        "scrollCollapse": true,
        "paging": false,
        "footer": false,
        "dom": '<"top">rt<"bottom"><"clear">'
    });

    // Toggle visibility of raw values columns
    $('#columns-toggle').on('click', function () {
        $(this).toggleClass('red')

        if (!cov_tables.tables(0).column(2).visible()) {
            $(this).attr("data-tooltip", "Hide Raw Depth Values");
        } else {
            $(this).attr("data-tooltip", "Show Raw Depth Values");
        }

        cov_tables.tables(0).columns('.toggle-cols').visible(!cov_tables.tables(0).column(2).visible());
        cov_tables.tables(1).columns('.toggle-cols').visible(!cov_tables.tables(1).column(2).visible());
    });

    // Set up custom search of both tables
    $('#mySearch').on('keyup click search', function () {
        $('#gene-table tbody tr').children('td').removeClass('row-selected')
        cov_tables.tables().search($(this).val()).draw();
    });

    // Hide raw value columns by default
    cov_tables.columns('.toggle-cols').visible(false)

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
        cov_tables.draw();
    })

    // Update tables when filter value modified
    $('#max-value').on('keyup click', function () {
        cov_tables.draw();
    });


    // Search exon table when select gene
    $('#gene-table tbody').on('click', 'tr', function (event) {
        var row = cov_tables.tables(0).row(this);
        var selected_gene = row.data()[0]

        if ($(this).children('td').hasClass('row-selected')) {
            $(this).children('td').removeClass('row-selected')
            cov_tables.tables(1).search('').draw()
        } else {
            $('#gene-table tbody tr').children('td').removeClass('row-selected')
            $(this).children('td').addClass('row-selected')
            cov_tables.tables(1).search(selected_gene).draw()
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