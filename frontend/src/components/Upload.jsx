import React, { useState } from "react";
import { uploadScript, analyzeScript } from "../api";

export default function Upload({ onAnalysisComplete }) {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [statusStep, setStatusStep] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [isDragging, setIsDragging] = useState(false);

    const onFileSelected = (selectedFile) => {
        if (!selectedFile) return;
        setFile(selectedFile);
        setErrorMessage("");
        setPreviewUrl(URL.createObjectURL(selectedFile));
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            onFileSelected(e.target.files[0]);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onFileSelected(e.dataTransfer.files[0]);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleUploadAndAnalyze = async () => {
        if (!file) return;

        setLoading(true);
        setErrorMessage("");

        try {
            // Step 1: Upload Image
            setStatusStep("Uploading script image to server...");
            const scriptData = await uploadScript(file);

            // Step 2: Trigger CV & Text Analysis
            setStatusStep("Extracting regions & running multimodal AI analysis...");
            await analyzeScript(scriptData.id);

            // Step 3: Callback to render results
            setStatusStep("Finalizing analysis...");
            onAnalysisComplete(scriptData.id);
        } catch (err) {
            setErrorMessage(err.message || "Failed to process the answer script. Please try again.");
        } finally {
            setLoading(false);
            setStatusStep("");
        }
    };

    return (
        <div
            style={{
                maxWidth: "560px",
                margin: "40px auto",
                padding: "32px",
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
                border: "1px solid #e1e4e8",
                textAlign: "center",
            }}
        >
            <h2 style={{ margin: "0 0 8px 0", fontSize: "22px", color: "#1f2937" }}>
                Upload Handwritten Answer Sheet
            </h2>
            <p style={{ margin: "0 0 24px 0", fontSize: "14px", color: "#6b7280" }}>
                Upload a scanned page or clear photo of student handwriting to extract text, tables, and diagrams.
            </p>

            {/* Drag & Drop Area */}
            <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => document.getElementById("file-input").click()}
                style={{
                    border: `2px dashed ${isDragging ? "#1a73e8" : file ? "#34a853" : "#d1d5db"}`,
                    backgroundColor: isDragging ? "#e8f0fe" : file ? "#f6fbf7" : "#fafafa",
                    borderRadius: "10px",
                    padding: "30px 20px",
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "all 0.2s ease",
                    marginBottom: "20px",
                }}
            >
                <input
                    id="file-input"
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    disabled={loading}
                    style={{ display: "none" }}
                />

                {previewUrl ? (
                    <div>
                        <img
                            src={previewUrl}
                            alt="Selected script preview"
                            style={{
                                maxHeight: "180px",
                                maxWidth: "100%",
                                borderRadius: "6px",
                                objectFit: "contain",
                                boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                                marginBottom: "12px",
                            }}
                        />
                        <div style={{ fontSize: "14px", fontWeight: "600", color: "#2d3748" }}>
                            {file.name}
                        </div>
                        <div style={{ fontSize: "12px", color: "#718096" }}>
                            {(file.size / 1024).toFixed(1)} KB — Click or drop another image to replace
                        </div>
                    </div>
                ) : (
                    <div>
                        <svg
                            style={{ width: "48px", height: "48px", margin: "0 auto 12px auto", color: "#9ca3af" }}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="1.5"
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                            />
                        </svg>
                        <div style={{ fontSize: "15px", fontWeight: "600", color: "#374151" }}>
                            Click to browse or drag & drop image here
                        </div>
                        <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "4px" }}>
                            Supports PNG, JPG, JPEG
                        </div>
                    </div>
                )}
            </div>

            {/* Action Button */}
            <button
                onClick={handleUploadAndAnalyze}
                disabled={!file || loading}
                style={{
                    width: "100%",
                    padding: "12px 24px",
                    fontSize: "15px",
                    fontWeight: "600",
                    color: "#ffffff",
                    backgroundColor: !file || loading ? "#9ca3af" : "#1a73e8",
                    border: "none",
                    borderRadius: "8px",
                    cursor: !file || loading ? "not-allowed" : "pointer",
                    transition: "background 0.2s ease",
                    boxShadow: !file || loading ? "none" : "0 2px 8px rgba(26, 115, 232, 0.3)",
                }}
            >
                {loading ? "Processing Answer Script..." : "Upload & Analyze Script"}
            </button>

            {/* Progress Status Indicator */}
            {loading && statusStep && (
                <div style={{ marginTop: "16px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", color: "#1a73e8", fontSize: "13px" }}>
                    <span style={{ display: "inline-block", width: "12px", height: "12px", border: "2px solid #1a73e8", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
                    <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
                    <span>{statusStep}</span>
                </div>
            )}

            {/* Error Message */}
            {errorMessage && (
                <div
                    style={{
                        marginTop: "16px",
                        padding: "10px 14px",
                        backgroundColor: "#fef2f2",
                        border: "1px solid #fee2e2",
                        borderRadius: "6px",
                        color: "#dc2626",
                        fontSize: "13px",
                        textAlign: "left",
                    }}
                >
                    <strong>Error:</strong> {errorMessage}
                </div>
            )}
        </div>
    );
}