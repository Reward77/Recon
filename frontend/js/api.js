// ============================================
// Recon API Configuration
// ============================================

const API_URL =
    window.RECON_API_URL ||
    "/api";


// ============================================
// API REQUEST HELPER
// ============================================

async function api(
    endpoint,
    method = "GET",
    body = null
) {

    // Your login should store the JWT here
    const token = localStorage.getItem("token");

    const options = {
        method: method,
        headers: {}
    };


    // ----------------------------------------
    // Authentication
    // ----------------------------------------

    if (token) {

        options.headers["Authorization"] =
            `Bearer ${token}`;

    }


    // ----------------------------------------
    // Request body
    // ----------------------------------------

    if (body instanceof FormData) {

        options.body = body;

    }

    else if (body !== null) {

        options.headers["Content-Type"] =
            "application/json";

        options.body =
            JSON.stringify(body);

    }


    // ----------------------------------------
    // Send request
    // ----------------------------------------

    let response;

    try {

        response = await fetch(
            API_URL + endpoint,
            options
        );

    }

    catch (error) {

        console.error(
            "Network error:",
            error
        );

        throw new Error(
            `Cannot connect to Recon API at ${API_URL}.`
        );

    }


    // ----------------------------------------
    // Read response
    // ----------------------------------------

    const contentType =
        response.headers.get("content-type") || "";

    let data = null;

    if (contentType.includes("application/json")) {

        data = await response.json();

    }

    else {

        data = await response.text();

    }


    // ----------------------------------------
    // Handle HTTP errors
    // ----------------------------------------

    if (!response.ok) {

        console.error(
            "API ERROR:",
            response.status,
            data
        );

        throw new Error(
            data?.detail ||
            data ||
            `Server error (${response.status})`
        );

    }


    return data;
}
