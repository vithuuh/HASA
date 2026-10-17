import React, { useState } from "react";
import Upload from "./components/Upload";
import Viewer from "./components/Viewer";

export default function App() {
    const [activeScriptId, setActiveScriptId] = useState(null);

    return (
        <div style={{ fontFamily: "sans-serif", padding: "20px" }}>
            <h1 style={{ textAlign: "center" }}>HASA - Handwritten Answer Script Analyzer</h1>
            {!activeScriptId ? (
                <Upload onAnalysisComplete={(id) => setActiveScriptId(id)} />
            ) : (
                <div>
                    <button onClick={() => setActiveScriptId(null)} style={{ marginBottom: "10px" }}>
                        Upload Another Script
                    </button>
                    <Viewer scriptId={activeScriptId} />
                </div>
            )}
        </div>
    );
}