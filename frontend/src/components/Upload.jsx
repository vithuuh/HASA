import React, { useState } from "react";
import { uploadScript, analyzeScript } from "../api";

export default function Upload({ onAnalysisComplete }) {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setErrorMessage("");
        }
    };

    const handleUploadAndAnalyze = async () => {
        if (!file) return;

        setLoading(true);
        setErrorMessage("");

        try {
            // Step 1: Upload Image
            const scriptData = await uploadScript(file);

            // Step 2: Trigger CV & Text Analysis
            await analyzeScript(scriptData.id);

            // Step 3: Callback to render results
            onAnalysisComplete(scriptData.id);
        } catch (err) {
            setErrorMessage("Process couldn't be completed.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: "20px", border: "1px solid #ccc", borderRadius: "8px", maxWidth: "500px", margin: "20px auto" }}>
            <h3>Upload Answer Script</h3>
            <input type="file" accept="image/*" onChange={handleFileChange} disabled={loading} />
            <br /><br />
            <button onClick={handleUploadAndAnalyze} disabled={!file || loading} style={{ padding: "10px 20px" }}>
                {loading ? "Processing..." : "Upload & Process"}
            </button>

            {errorMessage && <p style={{ color: "red", marginTop: "10px" }}>{errorMessage}</p>}
        </div>
    );
}