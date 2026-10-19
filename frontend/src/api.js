export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function uploadScript(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || `Upload failed with status ${response.status}`);
    }

    return response.json();
}

export async function analyzeScript(scriptId) {
    const response = await fetch(`${API_BASE_URL}/analyze/${scriptId}`, {
        method: "POST",
    });

    if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || `Analysis failed with status ${response.status}`);
    }

    return response.json();
}

export async function getScriptDetails(scriptId) {
    const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);

    if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || `Failed to fetch details with status ${response.status}`);
    }

    return response.json();
}