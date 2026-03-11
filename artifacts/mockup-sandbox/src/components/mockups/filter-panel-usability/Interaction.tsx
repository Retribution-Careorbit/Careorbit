import React, { useState, useEffect, useRef } from "react";
import { Search, X, Filter, ChevronDown, Check, Zap, Clock, ShieldCheck, Sparkles, XCircle } from "lucide-react";
import "./_group.css";

const CATEGORIES = ["unit", "functional", "integration", "e2e", "security", "business_logic", "regression", "other"];
const FEATURE_AREAS = ["Authentication", "Dashboard", "Medications", "Appointments", "Orbit Score", "Vitals", "Reminders", "Settings", "Notifications", "Reports"];

// Colors for category dots
const getCategoryColor = (cat: string) => {
  const map: Record<string, string> = {
    unit: "🟢",
    functional: "🔵",
    integration: "🟣",
    e2e: "🟠",
    security: "🔴",
    business_logic: "🟡",
    regression: "🟤",
    other: "⚪"
  };
  return map[cat] || "⚪";
};

// Mock counts for categories
const getCategoryCount = (cat: string) => {
  const hash = cat.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return (hash % 100) + 10;
};

// Mock counts for features
const getFeatureCount = (feat: string) => {
  const hash = feat.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return (hash % 50) + 5;
};

export function Interaction() {
  const [search, setSearch] = useState("");
  const [testName, setTestName] = useState("");
  const [filePath, setFilePath] = useState("");
  const [category, setCategory] = useState("");
  const [featureArea, setFeatureArea] = useState("");
  const [toggleFilter, setToggleFilter] = useState<"new" | "existing" | null>(null);
  
  const [unappliedChanges, setUnappliedChanges] = useState(false);

  // Quick chips
  const applyQuickFilter = (type: string) => {
    if (type === "new") {
      setToggleFilter("new");
    } else if (type === "unit") {
      setCategory("unit");
    } else if (type === "security") {
      setCategory("security");
    }
  };

  const handleClearAll = () => {
    setSearch("");
    setTestName("");
    setFilePath("");
    setCategory("");
    setFeatureArea("");
    setToggleFilter(null);
  };

  // Detect unapplied changes
  useEffect(() => {
    setUnappliedChanges(true);
  }, [search, testName, filePath, category, featureArea, toggleFilter]);

  const handleApply = () => {
    setUnappliedChanges(false);
  };

  const activeCount = [
    search, testName, filePath, category, featureArea, toggleFilter
  ].filter(Boolean).length;

  return (
    <div 
      className="relative flex flex-col font-sans overflow-hidden shadow-2xl"
      style={{
        width: "480px",
        height: "100vh",
        backgroundColor: "var(--bg-surface)",
        color: "var(--text-primary)",
        borderLeft: "1px solid var(--border-default)"
      }}
    >
      {/* Header */}
      <div 
        className="flex items-center justify-between px-6 py-5 shrink-0 relative z-10"
        style={{ borderBottom: "1px solid var(--border-default)", backgroundColor: "var(--bg-elevated)" }}
      >
        <div className="flex items-center gap-3">
          <div 
            className="flex items-center justify-center rounded-lg w-10 h-10 shadow-lg"
            style={{ backgroundColor: "var(--bg-base)", border: "1px solid var(--border-subtle)" }}
          >
            <Filter className="w-5 h-5" style={{ color: "var(--accent-cyan)" }} />
          </div>
          <h2 className="text-xl font-bold tracking-tight">Filters</h2>
          {activeCount > 0 && (
            <span 
              className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-bold transition-all duration-300 transform scale-100"
              style={{ backgroundColor: "var(--accent-cyan-dim)", color: "var(--accent-cyan)", border: "1px solid var(--accent-cyan)" }}
            >
              {activeCount}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <button 
              onClick={handleClearAll}
              className="text-sm font-medium hover:text-white transition-colors px-3 py-1.5 rounded-md"
              style={{ color: "var(--text-secondary)" }}
            >
              Reset
            </button>
          )}
          <button 
            className="p-2 rounded-md transition-colors hover:bg-white/5"
            style={{ color: "var(--text-secondary)" }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8 scrollbar-hide">
        
        {/* Quick Filters */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Quick Filters
          </label>
          <div className="flex flex-wrap gap-2">
            <QuickChip icon={<Sparkles className="w-3.5 h-3.5" />} label="New Only" onClick={() => applyQuickFilter("new")} />
            <QuickChip icon={<Zap className="w-3.5 h-3.5" />} label="Unit Tests" onClick={() => applyQuickFilter("unit")} />
            <QuickChip icon={<ShieldCheck className="w-3.5 h-3.5" />} label="Security" onClick={() => applyQuickFilter("security")} />
          </div>
        </div>

        {/* String Filters */}
        <div className="space-y-4 pt-2">
          <label className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Search & Match
          </label>
          
          <FloatingInput 
            label="Search All Fields" 
            value={search} 
            onChange={setSearch} 
            icon={<Search className="w-4 h-4" />}
          />
          <FloatingInput 
            label="Test Name Contains" 
            value={testName} 
            onChange={setTestName} 
          />
          <FloatingInput 
            label="File Path Contains" 
            value={filePath} 
            onChange={setFilePath} 
          />
        </div>

        {/* Dropdown Filters */}
        <div className="space-y-4 pt-2">
          <label className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Attributes
          </label>
          
          <NativeSelect 
            label="Category"
            value={category}
            onChange={setCategory}
            options={[
              { value: "", label: "Any Category" },
              ...CATEGORIES.map(c => ({
                value: c,
                label: `${getCategoryColor(c)} ${c} (${getCategoryCount(c)})`
              }))
            ]}
          />
          
          <NativeSelect 
            label="Feature Area"
            value={featureArea}
            onChange={setFeatureArea}
            options={[
              { value: "", label: "Any Feature Area" },
              ...FEATURE_AREAS.map(f => ({
                value: f,
                label: `${f} (${getFeatureCount(f)})`
              }))
            ]}
          />
        </div>

        {/* Toggle Filters */}
        <div className="space-y-4 pt-2">
          <label className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Test Status
          </label>
          
          <div className="flex flex-col gap-3">
            <button
              onClick={() => setToggleFilter(toggleFilter === "new" ? null : "new")}
              className={`flex items-center justify-between w-full p-4 rounded-xl border transition-all duration-200 group relative overflow-hidden ${
                toggleFilter === "new" 
                  ? "shadow-[0_0_15px_rgba(16,185,129,0.2)]" 
                  : "hover:shadow-lg"
              }`}
              style={{
                backgroundColor: toggleFilter === "new" ? "var(--accent-emerald-dim)" : "var(--bg-base)",
                borderColor: toggleFilter === "new" ? "var(--accent-emerald)" : "var(--border-strong)",
                transform: toggleFilter === "new" ? "scale(0.99)" : "scale(1)"
              }}
            >
              {/* Press effect overlay */}
              <div className="absolute inset-0 bg-white opacity-0 group-active:opacity-10 transition-opacity pointer-events-none" />
              
              <div className="flex items-center gap-3">
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center transition-colors"
                  style={{ 
                    backgroundColor: toggleFilter === "new" ? "var(--accent-emerald)" : "var(--bg-elevated)",
                    color: toggleFilter === "new" ? "#000" : "var(--text-secondary)"
                  }}
                >
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="flex flex-col items-start">
                  <span className="font-semibold text-sm" style={{ color: toggleFilter === "new" ? "var(--accent-emerald)" : "var(--text-primary)" }}>
                    New Tests Only
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Recently added tests</span>
                </div>
              </div>
              
              {toggleFilter === "new" && (
                <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: "var(--accent-emerald)", color: "#000" }}>
                  <Check className="w-3 h-3" />
                </div>
              )}
            </button>

            <button
              onClick={() => setToggleFilter(toggleFilter === "existing" ? null : "existing")}
              className={`flex items-center justify-between w-full p-4 rounded-xl border transition-all duration-200 group relative overflow-hidden ${
                toggleFilter === "existing" 
                  ? "shadow-[0_0_15px_rgba(245,158,11,0.2)]" 
                  : "hover:shadow-lg"
              }`}
              style={{
                backgroundColor: toggleFilter === "existing" ? "var(--accent-amber-dim)" : "var(--bg-base)",
                borderColor: toggleFilter === "existing" ? "var(--accent-amber)" : "var(--border-strong)",
                transform: toggleFilter === "existing" ? "scale(0.99)" : "scale(1)"
              }}
            >
              {/* Press effect overlay */}
              <div className="absolute inset-0 bg-white opacity-0 group-active:opacity-10 transition-opacity pointer-events-none" />
              
              <div className="flex items-center gap-3">
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center transition-colors"
                  style={{ 
                    backgroundColor: toggleFilter === "existing" ? "var(--accent-amber)" : "var(--bg-elevated)",
                    color: toggleFilter === "existing" ? "#000" : "var(--text-secondary)"
                  }}
                >
                  <Clock className="w-4 h-4" />
                </div>
                <div className="flex flex-col items-start">
                  <span className="font-semibold text-sm" style={{ color: toggleFilter === "existing" ? "var(--accent-amber)" : "var(--text-primary)" }}>
                    Existing Tests Only
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>Stable, older tests</span>
                </div>
              </div>
              
              {toggleFilter === "existing" && (
                <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: "var(--accent-amber)", color: "#000" }}>
                  <Check className="w-3 h-3" />
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Bottom padding for footer */}
        <div className="h-10" />
      </div>

      {/* Footer */}
      <div 
        className="px-6 py-5 shrink-0 grid grid-cols-3 gap-4 relative z-10"
        style={{ 
          backgroundColor: "var(--bg-elevated)", 
          borderTop: "1px solid var(--border-default)",
          boxShadow: "0 -10px 30px rgba(0,0,0,0.5)"
        }}
      >
        <button 
          onClick={handleClearAll}
          className="col-span-1 rounded-lg font-semibold text-sm py-3 transition-colors hover:bg-white/5"
          style={{ color: "var(--text-secondary)", border: "1px solid var(--border-strong)" }}
        >
          Clear All
        </button>
        <button 
          onClick={handleApply}
          className={`col-span-2 rounded-lg font-bold text-sm py-3 transition-all duration-300 relative overflow-hidden group ${
            unappliedChanges ? "animate-pulse shadow-[0_0_20px_rgba(0,212,255,0.4)]" : ""
          }`}
          style={{ 
            backgroundColor: unappliedChanges ? "var(--accent-cyan)" : "var(--bg-hover)", 
            color: unappliedChanges ? "#000" : "var(--text-primary)",
            transform: unappliedChanges ? "scale(1.02)" : "scale(1)"
          }}
        >
          {/* Shine effect */}
          <div className="absolute top-0 -inset-full h-full w-1/2 z-5 block transform -skew-x-12 bg-gradient-to-r from-transparent to-white opacity-20 group-hover:animate-[shine_1.5s_ease-in-out_infinite]" />
          Apply Filters {activeCount > 0 && `(${activeCount})`}
        </button>
      </div>

      <style dangerouslySetInnerHTML={{__html:`
        @keyframes shine {
          100% { left: 200%; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}} />
    </div>
  );
}

// Subcomponents

function QuickChip({ icon, label, onClick }: { icon: React.ReactNode, label: string, onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all hover:-translate-y-0.5"
      style={{ 
        backgroundColor: "var(--bg-elevated)", 
        border: "1px solid var(--border-strong)",
        color: "var(--text-primary)"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--accent-cyan)";
        e.currentTarget.style.boxShadow = "0 0 10px var(--accent-cyan-dim)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border-strong)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <span style={{ color: "var(--accent-cyan)" }}>{icon}</span>
      {label}
    </button>
  );
}

function FloatingInput({ label, value, onChange, icon }: { label: string, value: string, onChange: (v: string) => void, icon?: React.ReactNode }) {
  const [focused, setFocused] = useState(false);
  const active = focused || value.length > 0;

  return (
    <div className="relative group">
      <div 
        className="absolute inset-0 rounded-lg transition-opacity duration-300 opacity-0 group-hover:opacity-100 pointer-events-none"
        style={{ boxShadow: "0 0 15px var(--accent-cyan-dim)", border: "1px solid var(--accent-cyan)" }}
      />
      <div 
        className="relative flex items-center rounded-lg px-4 h-14 transition-colors duration-200"
        style={{ 
          backgroundColor: focused ? "var(--bg-base)" : "var(--bg-elevated)",
          border: `1px solid ${focused ? "var(--accent-cyan)" : "var(--border-strong)"}`
        }}
      >
        {icon && (
          <div className="mr-3" style={{ color: focused ? "var(--accent-cyan)" : "var(--text-muted)" }}>
            {icon}
          </div>
        )}
        <div className="relative flex-1 h-full">
          <label 
            className={`absolute left-0 transition-all duration-200 pointer-events-none flex items-center gap-1 font-medium ${
              active ? "-top-2 text-[10px]" : "top-4 text-sm"
            }`}
            style={{ 
              color: focused ? "var(--accent-cyan)" : "var(--text-muted)",
              backgroundColor: active ? (focused ? "var(--bg-base)" : "var(--bg-elevated)") : "transparent",
              padding: active ? "0 4px" : "0"
            }}
          >
            {label}
            {focused && !value && <span className="inline-block w-[1.5px] h-[10px] bg-cyan-400 animate-[blink_1s_step-end_infinite]" />}
          </label>
          <input 
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            className="w-full h-full bg-transparent outline-none text-sm pt-4 font-mono pb-1"
            style={{ color: "var(--text-primary)" }}
          />
        </div>
        
        {value && (
          <button 
            onClick={() => onChange("")}
            className="ml-2 p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10"
            style={{ color: "var(--text-muted)" }}
          >
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

function NativeSelect({ label, value, onChange, options }: { label: string, value: string, onChange: (v: string) => void, options: {value: string, label: string}[] }) {
  const [focused, setFocused] = useState(false);
  const active = focused || value.length > 0;

  return (
    <div className="relative group">
      <div 
        className="absolute inset-0 rounded-lg transition-opacity duration-300 opacity-0 group-hover:opacity-100 pointer-events-none"
        style={{ boxShadow: "0 0 15px var(--accent-violet-dim)", border: "1px solid var(--accent-violet)" }}
      />
      <div 
        className="relative flex items-center rounded-lg px-4 h-14 transition-colors duration-200"
        style={{ 
          backgroundColor: focused ? "var(--bg-base)" : "var(--bg-elevated)",
          border: `1px solid ${focused ? "var(--accent-violet)" : "var(--border-strong)"}`
        }}
      >
        <div className="relative flex-1 h-full flex flex-col justify-center">
          <label 
            className={`absolute left-0 transition-all duration-200 pointer-events-none flex items-center gap-1 font-medium z-10 ${
              active ? "-top-2 text-[10px]" : "top-4 text-sm"
            }`}
            style={{ 
              color: focused ? "var(--accent-violet)" : "var(--text-muted)",
              backgroundColor: active ? (focused ? "var(--bg-base)" : "var(--bg-elevated)") : "transparent",
              padding: active ? "0 4px" : "0"
            }}
          >
            {label}
          </label>
          
          <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            className="w-full h-full bg-transparent outline-none text-sm pt-4 pb-1 appearance-none cursor-pointer font-mono"
            style={{ color: "var(--text-primary)" }}
          >
            {options.map((opt, i) => (
              <option key={i} value={opt.value} style={{ backgroundColor: "var(--bg-elevated)", color: "var(--text-primary)" }}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center gap-1">
          {value && (
            <button 
              onClick={(e) => {
                e.stopPropagation();
                onChange("");
              }}
              className="p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10 z-20"
              style={{ color: "var(--text-muted)" }}
            >
              <XCircle className="w-4 h-4" />
            </button>
          )}
          <ChevronDown className="w-4 h-4 pointer-events-none" style={{ color: focused ? "var(--accent-violet)" : "var(--text-muted)" }} />
        </div>
      </div>
    </div>
  );
}
