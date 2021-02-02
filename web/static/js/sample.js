// ==============
// VARIANT FILTER 
// ============== 

$('#filter_button')
    .dropdown({
        action: 'activate',
        direction: 'downward',
        onChange: function (value, text, $selectedItem) {

            // do stuff when select value (extract filter attribute from selected item)

            var filterVal = $($selectedItem).data('filter')
        }
    });

$("#mod_filter").click(function () {
    $('.dropdown').blur();

    $('.dropdown').addClass('disabled')

    $('#variants-main-panel')
        .dimmer('show')
        ;
});

$("#filter-settings-close").click(function () {

    $('.dropdown').removeClass('disabled')

    $('#variants-main-panel')
        .dimmer('hide')
        ;
});


// ====================
// LOAD VARIANT DETAILS 
// ==================== 

$(document).ready(function () {

    $('.mini-tabs-link').click(function () {

        var tab_url = $(this).attr('data-url');
        var igv_search = $(this).attr('data-igv');

        if ($(this).hasClass('active')) {
            $('.mini-tabs-link').removeClass('active');
            $(".mini-tabs-content").hide();
            $("#variant-content-loader").removeClass('active');
            $(".basic_message").show();
        } else {
            $('.mini-tabs-link').removeClass('active');
            $(this).addClass('active');

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

                    clearTimeout(ajaxLoadTimeout);
                    $("#variant-content-loader").removeClass('active');

                    igv.browser.search(igv_search);
                }
            });
        }
    })

})

// Hide non-active tabs initially
$('.mini-tabs-content').hide()

$('#menu-toggle-open').click(function () {
    $('#variant-menu').hide()
    $('.menu-toggle-closed').show()
})

$('.menu-toggle-closed').click(function () {
    $('#variant-menu').show()
    $('.menu-toggle-closed').hide()


    // to keep the filter working
    $('.gene').show()
    $('.mini-tabs-link').show().filter(".hidden").hide()
    $('.gene').each(function () {
        return $(this).toggle($('.item.mini-tabs-link:visible', this).length != 0);
    });
})

$('.menu-toggle-closed').hide()

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
    igv.visibilityChange();
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
    igv.visibilityChange();
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
    $('#mySearch').on('keyup click', function () {
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
