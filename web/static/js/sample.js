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

        // Load variant details from link and format it for jbrowse
        var chr = $(this).attr('data-chr');
        var location = $(this).attr('data-location');
        var left = +location - 5;
        var right = +location + 4;
        var coords = chr + ":" + left + '..' + right;

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

                    // Navigate jbrowse to variant coords
                    genomeView.view.navToLocString(coords);
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

    // Trigger resize to force jbrowse to update width.
    window.dispatchEvent(new Event('resize'));


    // Reset position of browser to that of active variant. 
    var chr = $('.mini-tabs-link.active').attr('data-chr');
    var location = $('.mini-tabs-link.active').attr('data-location');
    var left = +location - 5;
    var right = +location + 4;
    var coords = chr + ":" + left + '..' + right;

    // Delay by 1s to ensure browser is loaded first.
    setTimeout(function () { genomeView.view.navToLocString(coords); }, 1000);

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
    location: '1'
})