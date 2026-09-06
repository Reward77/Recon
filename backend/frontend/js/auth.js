function getToken() {

    return localStorage.getItem("token");

}

function logout() {

    localStorage.removeItem("token");

    window.location.href = "index.html";

}

function protectPage() {

    if (!getToken()) {

        window.location.href = "index.html";

    }

}