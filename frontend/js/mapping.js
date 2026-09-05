protectPage();

let jobs = [];
let uploads = [];

let companyColumns = [];
let processorColumns = [];
let processorColumnSets = {};
let processorMappings = {};

let selectedJobId = null;
let selectedCompanyFile = null;
let selectedProcessorFiles = [];


document.addEventListener("DOMContentLoaded", async () => {

    await loadJobs();

    document
        .getElementById("jobSelect")
        .addEventListener(
            "change",
            handleJobChange
        );

    document
        .getElementById("detectColumnsBtn")
        .addEventListener(
            "click",
            detectColumns
        );

    document
        .getElementById("saveMappingBtn")
        .addEventListener(
            "click",
            saveMapping
        );

    document
        .getElementById("resetMappingBtn")
        .addEventListener(
            "click",
            resetMapping
        );

});


/* =========================================
   LOAD JOBS
========================================= */

async function loadJobs() {

    try {

        const response = await api("/jobs");

        if (Array.isArray(response)) {
            jobs = response;
        }
        else if (Array.isArray(response?.jobs)) {
            jobs = response.jobs;
        }
        else {
            jobs = [];
        }

        const select =
            document.getElementById("jobSelect");

        select.innerHTML = `
            <option value="">
                Select a reconciliation job
            </option>
        `;

        jobs.forEach(job => {

            const option =
                document.createElement("option");

            option.value = job.id;

            option.textContent =
                job.job_name ||
                job.name ||
                "Unnamed Job";

            select.appendChild(option);

        });

    }
    catch (error) {

        console.error(
            "Failed to load jobs:",
            error
        );

        alert(
            error.message ||
            "Unable to load jobs."
        );

    }

}


/* =========================================
   JOB CHANGE
========================================= */

async function handleJobChange(event) {

    selectedJobId =
        event.target.value;

    resetMapping();

    if (!selectedJobId) {

        document.getElementById(
            "fileSection"
        ).style.display = "none";

        return;
    }

    document.getElementById(
        "fileSection"
    ).style.display = "block";


    await loadUploadsForJob(
        selectedJobId
    );

}


/* =========================================
   LOAD UPLOADS
========================================= */

async function loadUploadsForJob(jobId) {

    try {

        const response =
            await api(`/uploads/job/${jobId}`);


        if (Array.isArray(response)) {
            uploads = response;
        }
        else if (Array.isArray(response?.uploads)) {
            uploads = response.uploads;
        }
        else {
            uploads = [];
        }


        const jobUploads =
            uploads.filter(upload => {

                const uploadJobId =
                    upload.job_id ||
                    upload.job?.id;

                return String(uploadJobId)
                    === String(jobId);

            });


        populateFileSelects(
            jobUploads
        );

        updateSelectedFilePreview();

    }
    catch (error) {

        console.error(
            "Failed to load uploads:",
            error
        );

        alert(
            error.message ||
            "Unable to load uploads."
        );

    }

}


/* =========================================
   POPULATE FILES
========================================= */

function populateFileSelects(jobUploads) {

    const companySelect =
        document.getElementById(
            "companyFile"
        );

    const processorSelect =
        document.getElementById(
            "processorFile"
        );


    companySelect.innerHTML = `
        <option value="">
            Select company file
        </option>
    `;

    processorSelect.innerHTML = `
        <option value="">
            Select processor file
        </option>
    `;


    jobUploads.forEach(upload => {

        const type =
            String(
                upload.file_type ||
                upload.upload_type ||
                upload.type ||
                ""
            ).toLowerCase();


        const fileName =
            upload.original_filename ||
            upload.filename ||
            upload.file_name ||
            "Unnamed file";


        const option =
            document.createElement("option");

        option.value =
            upload.id;

        option.textContent =
            fileName;


        if (type === "company") {

            companySelect.appendChild(
                option
            );

        }
        else if (type === "processor") {

            processorSelect.appendChild(
                option
            );

        }

    });

    companySelect.onchange = updateSelectedFilePreview;
    processorSelect.onchange = updateSelectedFilePreview;

}


function updateSelectedFilePreview() {
    const companyOption =
        document.getElementById(
            "companyFile"
        );
    const processorOption =
        document.getElementById(
            "processorFile"
        );

    const companyLabel =
        companyOption.selectedOptions[0]?.textContent ||
        "No file selected";
    const processorLabel = Array.from(processorOption.selectedOptions)
        .map(option => option.textContent).join(", ") || "No file selected";

    document.getElementById(
        "companyFileName"
    ).innerText =
        companyOption.value
            ? companyLabel
            : "No file selected";

    document.getElementById(
        "processorFileName"
    ).innerText =
        processorOption.value
            ? processorLabel
            : "No file selected";
}


async function detectColumns() {
    selectedCompanyFile =
        document.getElementById(
            "companyFile"
        ).value;

    selectedProcessorFiles = Array.from(document.getElementById("processorFile").selectedOptions)
        .map(option => option.value).filter(Boolean);

    if (!selectedCompanyFile) {
        alert(
            "Please select a company file."
        );
        return;
    }

    if (!selectedProcessorFiles.length) {
        alert(
            "Please select a processor file."
        );
        return;
    }

    const button =
        document.getElementById(
            "detectColumnsBtn"
        );

    button.disabled = true;
    button.innerText =
        "Detecting columns...";

    try {
        const response =
            await api(
                `/uploads/${selectedCompanyFile}/columns`
            );

        companyColumns =
            response.company_columns ||
            response.columns ||
            [];

        processorColumnSets = {};
        await Promise.all(selectedProcessorFiles.map(async fileId => {
            const processorResponse = await api(`/uploads/${fileId}/columns`);
            processorColumnSets[fileId] = processorResponse.columns || [];
        }));
        const mappingProcessorSelect = document.getElementById("mappingProcessorFile");
        mappingProcessorSelect.innerHTML = "";
        selectedProcessorFiles.forEach(fileId => {
            const source = document.querySelector(`#processorFile option[value="${fileId}"]`);
            const option = new Option(source?.textContent || fileId, fileId);
            mappingProcessorSelect.add(option);
        });
        processorMappings = {};
        processorColumns = processorColumnSets[selectedProcessorFiles[0]];
        mappingProcessorSelect.onchange = switchProcessorMapping;

        populateColumnSelects();

        document.getElementById(
            "mappingSection"
        ).style.display = "block";

        document.getElementById(
            "mappingSection"
        ).scrollIntoView({
            behavior: "smooth"
        });
    }
    catch (error) {
        console.error(
            "Column detection failed:",
            error
        );

        alert(
            error.message ||
            "Unable to detect file columns."
        );
    }
    finally {
        button.disabled = false;
        button.innerText =
            "Detect Columns";
    }
}


/* =========================================
   POPULATE COLUMN DROPDOWNS
========================================= */

function populateColumnSelects() {

    const companyFields = [
        "company_transaction_id",
        "company_amount",
        "company_status",
        "company_date",
        "company_reference"
    ];

    const processorFields = [
        "processor_transaction_id",
        "processor_amount",
        "processor_status",
        "processor_date",
        "processor_reference"
    ];


    companyFields.forEach(id => {

        populateSelect(
            document.getElementById(id),
            companyColumns
        );

    });


    processorFields.forEach(id => {

        populateSelect(
            document.getElementById(id),
            processorColumns
        );

    });

}

function currentProcessorMapping() {
    return {
        transaction_id: getValue("processor_transaction_id"), amount: getValue("processor_amount"),
        status: getValue("processor_status"), date: getValue("processor_date"), reference: getValue("processor_reference")
    };
}

function hasRequiredProcessorMapping(mapping) {
    return Boolean(mapping?.transaction_id && mapping?.amount && mapping?.status);
}

function switchProcessorMapping(event) {
    const previousFile = Object.keys(processorColumnSets).find(fileId => processorColumns === processorColumnSets[fileId]);
    if (previousFile) processorMappings[previousFile] = currentProcessorMapping();
    const fileId = event.target.value;
    processorColumns = processorColumnSets[fileId] || [];
    ["processor_transaction_id", "processor_amount", "processor_status", "processor_date", "processor_reference"]
        .forEach(id => populateSelect(document.getElementById(id), processorColumns));
    const saved = processorMappings[fileId] || {};
    Object.entries(saved).forEach(([field, value]) => document.getElementById(`processor_${field}`).value = value);
}


/* =========================================
   SELECT HELPER
========================================= */

function populateSelect(
    select,
    columns
) {

    select.innerHTML = `
        <option value="">
            Select column
        </option>
    `;


    columns.forEach(column => {

        const option =
            document.createElement("option");

        option.value = column;

        option.textContent = column;

        select.appendChild(option);

    });

}


/* =========================================
   SAVE MAPPING
========================================= */

async function saveMapping() {

    const mapping = {

        job_id: selectedJobId,

        company_file_id:
            selectedCompanyFile,

        processor_file_ids: selectedProcessorFiles,

        company: {

            transaction_id:
                getValue(
                    "company_transaction_id"
                ),

            amount:
                getValue(
                    "company_amount"
                ),

            status:
                getValue(
                    "company_status"
                ),

            date:
                getValue(
                    "company_date"
                ),

            reference:
                getValue(
                    "company_reference"
                )

        },

        processors: {}

    };


    if (
        !mapping.company.transaction_id ||
        !getValue("processor_transaction_id")
    ) {

        alert(
            "Transaction ID must be mapped on both files."
        );

        return;

    }


    if (
        !mapping.company.amount ||
        !getValue("processor_amount")
    ) {

        alert(
            "Amount must be mapped on both files."
        );

        return;

    }

    const activeFileId = document.getElementById("mappingProcessorFile").value;
    processorMappings[activeFileId] = currentProcessorMapping();
    mapping.processors = processorMappings;
    const unmapped = selectedProcessorFiles.find(fileId =>
        !hasRequiredProcessorMapping(mapping.processors[fileId])
    );
    if (unmapped) {
        alert("Map the required fields for every selected processor file before saving.");
        return;
    }


    const button =
        document.getElementById(
            "saveMappingBtn"
        );

    button.disabled = true;

    button.innerText =
        "Saving...";


    try {

        /*
         * Backend endpoint expected:
         *
         * POST /mapping
         */

        const response =
            await api(
                "/mapping",
                "POST",
                mapping
            );


        console.log(
            "Mapping saved:",
            response
        );


        document.getElementById(
            "mappingStatus"
        ).innerText =
            "Mapping complete";


        document.getElementById(
            "mappingStatus"
        ).style.background =
            "#dcfce7";


        document.getElementById(
            "mappingStatus"
        ).style.color =
            "#166534";


        document.getElementById(
            "mappingSummary"
        ).style.display =
            "flex";


    }
    catch (error) {

        console.error(
            "Failed to save mapping:",
            error
        );

        alert(
            error.message ||
            "Unable to save mapping."
        );

    }
    finally {

        button.disabled = false;

        button.innerText =
            "Save Mapping";

    }

}


/* =========================================
   RESET
========================================= */

function resetMapping() {

    document.getElementById(
        "mappingSection"
    ).style.display = "none";


    document.getElementById(
        "mappingSummary"
    ).style.display = "none";


    document.getElementById(
        "mappingStatus"
    ).innerText =
        "Not saved";


    companyColumns = [];

    processorColumns = [];
    processorColumnSets = {};
    processorMappings = {};
    selectedProcessorFiles = [];

}


/* =========================================
   HELPER
========================================= */

function getValue(id) {

    return document
        .getElementById(id)
        .value;

}
