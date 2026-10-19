import React, { useEffect, useState } from "react";
import { getScriptDetails } from "../api";

export default function Viewer({ scriptId }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
        if (scriptId) {
            getScriptDetails(scriptId)
                .then((res) => setData(res))
                .catch(() => setError("Process couldn't be completed."));
        }
    }, [scriptId]);

    if (error) return <p style={{ color: "red" }}>{error}</p>;
    if (!data) return <p>Loading processed data...</p>;

    const imageUrl = `http://localhost:8000/uploads/${data.script.filename}`;

    return (
        <div style={{ display: "flex", gap: "20px", padding: "20px" }}>
            {/* Left Column: Image with Bounding Box Overlays */}
            <div style={{ flex: 1, position: "relative" }}>
                <h4>Original Answer Sheet</h4>
                <div style={{ position: "relative", display: "inline-block" }}>
                    <img src={imageUrl} alt="Uploaded Script" style={{ maxWidth: "100%", height: "auto" }} />
                    {data.regions.map((reg) => (
                        <div
                            key={reg.id}
                            style={{
                                position: "absolute",
                                left: `${reg.bbox_x}px`,
                                top: `${reg.bbox_y}px`,
                                width: `${reg.bbox_w}px`,
                                height: `${reg.bbox_h}px`,
                                border: "2px solid red",
                                backgroundColor: "rgba(255, 0, 0, 0.1)",
                                pointerEvents: "none",
                            }}
                        >
                            <span style={{ backgroundColor: "red", color: "white", fontSize: "10px", padding: "2px" }}>
                                #{reg.order_index + 1}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right Column: Structured Parsed Results */}
            <div style={{ flex: 1, overflowY: "auto", maxHeight: "80vh" }}>
                <h4>Parsed Content</h4>
                {data.regions.map((reg) => (
                    <div key={reg.id} style={{ marginBottom: "15px", padding: "10px", border: "1px solid #ddd", borderRadius: "5px" }}>
                        <strong>Region #{reg.order_index + 1} ({reg.region_type})</strong>
                        <pre style={{ whiteSpace: "pre-wrap", background: "#f5f5f5", padding: "8px" }}>
                            {reg.refined_content || reg.raw_ocr_text || "Process couldn't be completed."}
                        </pre>
                    </div>
                ))}
            </div>
        </div>
    );
}