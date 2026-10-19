import React, { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getScriptDetails, API_BASE_URL } from "../api";

export default function Viewer({ scriptId }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState("");
    const [selectedRegionId, setSelectedRegionId] = useState(null);
    const [hoveredRegionId, setHoveredRegionId] = useState(null);
    const [showRawOcr, setShowRawOcr] = useState(false);
    const [imgDimensions, setImgDimensions] = useState({ width: 0, height: 0 });

    const cardRefs = useRef({});

    useEffect(() => {
        if (scriptId) {
            getScriptDetails(scriptId)
                .then((res) => setData(res))
                .catch((err) => setError(err.message || "Failed to load script details."));
        }
    }, [scriptId]);

    const handleImageLoad = (e) => {
        setImgDimensions({
            width: e.target.naturalWidth,
            height: e.target.naturalHeight,
        });
    };

    const handleSelectRegion = (regionId) => {
        setSelectedRegionId(regionId);
        if (cardRefs.current[regionId]) {
            cardRefs.current[regionId].scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    };

    if (error) {
        return (
            <div style={{ padding: "20px", color: "#d9534f", background: "#fdf7f7", borderRadius: "8px", border: "1px solid #f5c6cb" }}>
                <strong>Error:</strong> {error}
            </div>
        );
    }

    if (!data) {
        return (
            <div style={{ textAlign: "center", padding: "40px", color: "#555" }}>
                <div style={{ fontSize: "18px", fontWeight: "600" }}>Loading script analysis...</div>
                <p style={{ color: "#888", marginTop: "8px" }}>Fetching layout detection & multimodal transcriptions</p>
            </div>
        );
    }

    const imageUrl = `${API_BASE_URL}/uploads/${data.script.filename}`;
    const activeRegion = selectedRegionId ?? hoveredRegionId;

    const getTypeColor = (type) => {
        switch (type) {
            case "header":
                return { bg: "#fef3c7", text: "#b45309", border: "#f59e0b" };
            case "question":
                return { bg: "#ede9fe", text: "#6d28d9", border: "#8b5cf6" };
            case "markdown_table":
            case "table":
                return { bg: "#e6f4ea", text: "#137333", border: "#34a853" };
            case "diagram":
                return { bg: "#fce7f3", text: "#be185d", border: "#ec4899" };
            default:
                return { bg: "#e8f0fe", text: "#1a73e8", border: "#4285f4" };
        }
    };


    return (
        <div style={{ display: "flex", gap: "24px", marginTop: "16px", alignItems: "flex-start" }}>
            {/* Left Column: Image with Interactive SVG Bounding Box Overlays */}
            <div
                style={{
                    flex: "1 1 50%",
                    background: "#ffffff",
                    borderRadius: "10px",
                    boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
                    padding: "16px",
                    border: "1px solid #e1e4e8",
                }}
            >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <h3 style={{ margin: 0, fontSize: "16px", color: "#333" }}>
                        Original Answer Sheet ({data.regions?.length || 0} detected regions)
                    </h3>
                    <span style={{ fontSize: "12px", color: "#777" }}>
                        Click a region on image or card to highlight
                    </span>
                </div>

                <div style={{ position: "relative", width: "100%", overflow: "hidden", borderRadius: "6px" }}>
                    <img
                        src={imageUrl}
                        alt="Uploaded Script"
                        onLoad={handleImageLoad}
                        style={{ width: "100%", height: "auto", display: "block" }}
                    />

                    {imgDimensions.width > 0 && (
                        <svg
                            style={{
                                position: "absolute",
                                top: 0,
                                left: 0,
                                width: "100%",
                                height: "100%",
                            }}
                            viewBox={`0 0 ${imgDimensions.width} ${imgDimensions.height}`}
                        >
                            {data.regions.map((reg) => {
                                const isCurrent = activeRegion === reg.id;
                                const isSelected = selectedRegionId === reg.id;
                                const colors = getTypeColor(reg.region_type);

                                return (
                                    <g
                                        key={reg.id}
                                        style={{ cursor: "pointer", transition: "all 0.15s ease" }}
                                        onClick={() => handleSelectRegion(reg.id)}
                                        onMouseEnter={() => setHoveredRegionId(reg.id)}
                                        onMouseLeave={() => setHoveredRegionId(null)}
                                    >
                                        <rect
                                            x={reg.bbox_x}
                                            y={reg.bbox_y}
                                            width={reg.bbox_w}
                                            height={reg.bbox_h}
                                            fill={isCurrent ? "rgba(66, 133, 244, 0.25)" : "rgba(234, 67, 53, 0.12)"}
                                            stroke={isSelected ? "#1a73e8" : isCurrent ? "#4285f4" : colors.border}
                                            strokeWidth={isCurrent ? "4" : "2"}
                                            strokeDasharray={isCurrent ? "none" : "4 2"}
                                            rx="4"
                                        />
                                        <rect
                                            x={reg.bbox_x + 4}
                                            y={reg.bbox_y + 4}
                                            width={44}
                                            height={22}
                                            fill={isCurrent ? "#1a73e8" : colors.border}
                                            rx="3"
                                        />
                                        <text
                                            x={reg.bbox_x + 26}
                                            y={reg.bbox_y + 20}
                                            fill="white"
                                            fontSize="13"
                                            fontWeight="bold"
                                            textAnchor="middle"
                                        >
                                            #{reg.order_index + 1}
                                        </text>
                                    </g>
                                );
                            })}
                        </svg>
                    )}
                </div>
            </div>

            {/* Right Column: Structured Parsed Cards */}
            <div
                style={{
                    flex: "1 1 50%",
                    maxHeight: "85vh",
                    overflowY: "auto",
                    paddingRight: "8px",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        position: "sticky",
                        top: 0,
                        background: "#f4f6f8",
                        padding: "8px 0 12px 0",
                        zIndex: 10,
                    }}
                >
                    <h3 style={{ margin: 0, fontSize: "16px", color: "#333" }}>Parsed Analysis Results</h3>
                    <label style={{ fontSize: "13px", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}>
                        <input
                            type="checkbox"
                            checked={showRawOcr}
                            onChange={(e) => setShowRawOcr(e.target.checked)}
                        />
                        Show Raw Tesseract OCR
                    </label>
                </div>

                {data.regions.map((reg) => {
                    const isCurrent = activeRegion === reg.id;
                    const isSelected = selectedRegionId === reg.id;
                    const colors = getTypeColor(reg.region_type);

                    return (
                        <div
                            key={reg.id}
                            ref={(el) => (cardRefs.current[reg.id] = el)}
                            onClick={() => handleSelectRegion(reg.id)}
                            onMouseEnter={() => setHoveredRegionId(reg.id)}
                            onMouseLeave={() => setHoveredRegionId(null)}
                            style={{
                                marginBottom: "14px",
                                padding: "14px",
                                borderRadius: "8px",
                                border: isSelected
                                    ? "2px solid #1a73e8"
                                    : isCurrent
                                    ? "2px solid #90caf9"
                                    : "1px solid #e0e0e0",
                                backgroundColor: isSelected ? "#f8fbff" : "#ffffff",
                                boxShadow: isCurrent ? "0 4px 12px rgba(66, 133, 244, 0.15)" : "0 1px 3px rgba(0,0,0,0.04)",
                                transition: "all 0.2s ease",
                                cursor: "pointer",
                            }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <span
                                        style={{
                                            fontWeight: "700",
                                            fontSize: "14px",
                                            color: isCurrent ? "#1a73e8" : "#333",
                                        }}
                                    >
                                        Region #{reg.order_index + 1}
                                    </span>
                                    <span
                                        style={{
                                            fontSize: "11px",
                                            fontWeight: "600",
                                            color: colors.text,
                                            backgroundColor: colors.bg,
                                            border: `1px solid ${colors.border}40`,
                                            padding: "2px 8px",
                                            borderRadius: "12px",
                                            textTransform: "uppercase",
                                        }}
                                    >
                                        {reg.region_type === "markdown_table" ? "Table" : reg.region_type}
                                    </span>
                                </div>
                                <span style={{ fontSize: "11px", color: "#888" }}>
                                    {reg.bbox_w}×{reg.bbox_h} px
                                </span>
                            </div>

                            {/* Render Gemini's Refined Output as Markdown */}
                            <div
                                style={{
                                    fontSize: "14px",
                                    lineHeight: "1.6",
                                    color: "#24292e",
                                    overflowX: "auto",
                                }}
                            >
                                {reg.refined_content ? (
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            table: ({ node, ...props }) => (
                                                <table
                                                    style={{
                                                        borderCollapse: "collapse",
                                                        width: "100%",
                                                        margin: "8px 0",
                                                        fontSize: "13px",
                                                        border: "1px solid #d0d7de",
                                                    }}
                                                    {...props}
                                                />
                                            ),
                                            th: ({ node, ...props }) => (
                                                <th
                                                    style={{
                                                        border: "1px solid #d0d7de",
                                                        padding: "6px 10px",
                                                        background: "#f6f8fa",
                                                        fontWeight: "600",
                                                    }}
                                                    {...props}
                                                />
                                            ),
                                            td: ({ node, ...props }) => (
                                                <td
                                                    style={{
                                                        border: "1px solid #d0d7de",
                                                        padding: "6px 10px",
                                                    }}
                                                    {...props}
                                                />
                                            ),
                                            p: ({ node, ...props }) => <p style={{ margin: "4px 0" }} {...props} />,
                                        }}
                                    >
                                        {reg.refined_content}
                                    </ReactMarkdown>
                                ) : (
                                    <span style={{ fontStyle: "italic", color: "#888" }}>
                                        No text could be extracted for this region.
                                    </span>
                                )}
                            </div>

                            {/* Optional Raw OCR Drawer */}
                            {showRawOcr && reg.raw_ocr_text && (
                                <div
                                    style={{
                                        marginTop: "10px",
                                        padding: "8px 10px",
                                        background: "#fafafa",
                                        borderRadius: "4px",
                                        border: "1px dashed #ccc",
                                        fontSize: "12px",
                                        color: "#666",
                                    }}
                                >
                                    <strong>Raw Tesseract OCR:</strong>
                                    <pre style={{ margin: "4px 0 0 0", whiteSpace: "pre-wrap", fontFamily: "monospace" }}>
                                        {reg.raw_ocr_text}
                                    </pre>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}