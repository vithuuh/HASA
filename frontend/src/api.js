const API_BASE_URL = "http://localhost:8000";

export async function uploadScript(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error("Process couldn't be completed.");
    }

    return response.json();
}

export async function analyzeScript(scriptId) {
    const response = await fetch(`${API_BASE_URL}/analyze/${scriptId}`, {
        method: "POST",
    });

    if (!response.ok) {
        throw new Error("Process couldn't be completed.");
    }

    return response.json();
}

export async function getScriptDetails(scriptId) {
    const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);

    if (!response.ok) {
        throw new Error("Process couldn't be completed.");
    }

    return response.json();
}