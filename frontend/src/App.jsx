import React, { useState } from "react";
import Upload from "./components/Upload";
import Viewer from "./components/Viewer";

export default function App() {
    const [activeScriptId, setActiveScriptId] = useState(null);

    return (
        <div style={{ minHeight: "100vh", backgroundColor: "#f8fafc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", color: "#1e293b" }}>
            {/* Header */}
            <header
                style={{
                    backgroundColor: "#ffffff",
                    borderBottom: "1px solid #e2e8f0",
                    padding: "16px 28px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                        style={{
                            width: "34px",
                            height: "34px",
                            borderRadius: "8px",
                            background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "white",
                            fontWeight: "bold",
                            fontSize: "16px",
                        }}
                    >
                        H
                    </div>
                    <div>
                        <h1 style={{ margin: 0, fontSize: "18px", fontWeight: "700", color: "#0f172a" }}>
                            HASA
                        </h1>
                        <span style={{ fontSize: "11px", color: "#64748b" }}>
                            Handwritten Answer Script Analyzer & Evaluator
                        </span>
                    </div>
                </div>

                {activeScriptId && (
                    <button
                        onClick={() => setActiveScriptId(null)}
                        style={{
                            padding: "8px 16px",
                            fontSize: "13px",
                            fontWeight: "600",
                            color: "#2563eb",
                            backgroundColor: "#eff6ff",
                            border: "1px solid #bfdbfe",
                            borderRadius: "6px",
                            cursor: "pointer",
                            transition: "all 0.2s ease",
                        }}
                    >
                        + Upload Another Script
                    </button>
                )}
            </header>

            {/* Main Content Area */}
            <main style={{ padding: "24px 28px", maxWidth: "1600px", margin: "0 auto" }}>
                {!activeScriptId ? (
                    <Upload onAnalysisComplete={(id) => setActiveScriptId(id)} />
                ) : (
                    <Viewer scriptId={activeScriptId} />
                )}
            </main>
        </div>
    );
}