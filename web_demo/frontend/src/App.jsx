import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const DEFAULT_FORM = {
  marital_status: 1,
  application_mode: 1,
  application_order: 1,
  course: 9238,
  daytime_evening_attendance: 1,
  previous_qualification: 1,
  previous_qualification_grade: 120,
  nacionality: 1,
  mothers_qualification: 1,
  fathers_qualification: 1,
  mothers_occupation: 4,
  fathers_occupation: 4,
  admission_grade: 120,
  displaced: 0,
  educational_special_needs: 0,
  debtor: 0,
  tuition_fees_up_to_date: 1,
  gender: 0,
  scholarship_holder: 0,
  age_at_enrollment: 20,
  international: 0,
  curricular_units_1st_sem_credited: 0,
  curricular_units_1st_sem_enrolled: 6,
  curricular_units_1st_sem_evaluations: 6,
  curricular_units_1st_sem_approved: 5,
  curricular_units_1st_sem_grade: 12,
  curricular_units_1st_sem_without_evaluations: 0,
  curricular_units_2nd_sem_credited: 0,
  curricular_units_2nd_sem_enrolled: 6,
  curricular_units_2nd_sem_evaluations: 6,
  curricular_units_2nd_sem_approved: 5,
  curricular_units_2nd_sem_grade: 12,
  curricular_units_2nd_sem_without_evaluations: 0,
  unemployment_rate: 10,
  inflation_rate: 1,
  gdp: 1,
};

const sections = [
  {
    title: "Admission / Tuyển sinh",
    fields: [
      ["select", "marital_status", "Marital status / Tình trạng hôn nhân", "marital_status"],
      ["select", "application_mode", "Application mode / Hình thức nhập học", "application_mode"],
      ["number", "application_order", "Application order / Thứ tự nguyện vọng", { min: 0, max: 9, step: 1 }],
      ["select", "course", "Course / Ngành học", "course"],
      ["selectStatic", "daytime_evening_attendance", "Daytime/evening attendance / Hệ học", { 1: "Daytime / Ban ngày", 0: "Evening / Buổi tối" }],
      ["select", "previous_qualification", "Previous qualification / Văn bằng trước đó", "previous_qualification"],
      ["number", "previous_qualification_grade", "Previous qualification grade / Điểm văn bằng trước đó", { min: 0, max: 200, step: 0.1 }],
      ["number", "admission_grade", "Admission grade / Điểm đầu vào", { min: 0, max: 200, step: 0.1 }],
      ["select", "nacionality", "Nationality / Quốc tịch", "nacionality"],
    ],
  },
  {
    title: "Student profile / Hồ sơ sinh viên",
    fields: [
      ["selectStatic", "gender", "Gender / Giới tính", { 0: "Female / Nữ", 1: "Male / Nam" }],
      ["number", "age_at_enrollment", "Age at enrollment / Tuổi khi nhập học", { min: 15, max: 80, step: 1 }],
      ["selectStatic", "displaced", "Displaced / Xa nhà hoặc di chuyển nơi ở?", { 0: "No / Không", 1: "Yes / Có" }],
      ["selectStatic", "educational_special_needs", "Educational special needs / Nhu cầu giáo dục đặc biệt?", { 0: "No / Không", 1: "Yes / Có" }],
      ["selectStatic", "international", "International / Sinh viên quốc tế?", { 0: "No / Không", 1: "Yes / Có" }],
      ["select", "mothers_qualification", "Mother's qualification / Trình độ học vấn của mẹ", "mothers_qualification"],
      ["select", "fathers_qualification", "Father's qualification / Trình độ học vấn của bố", "fathers_qualification"],
      ["select", "mothers_occupation", "Mother's occupation / Nghề nghiệp của mẹ", "mothers_occupation"],
      ["select", "fathers_occupation", "Father's occupation / Nghề nghiệp của bố", "fathers_occupation"],
      ["selectStatic", "debtor", "Debtor / Đang nợ học phí hoặc khoản phí?", { 0: "No / Không", 1: "Yes / Có" }],
      ["selectStatic", "tuition_fees_up_to_date", "Tuition fees up to date / Đã đóng học phí đúng hạn?", { 0: "No / Không", 1: "Yes / Có" }],
      ["selectStatic", "scholarship_holder", "Scholarship holder / Có học bổng?", { 0: "No / Không", 1: "Yes / Có" }],
    ],
  },
  {
    title: "Academic results / Kết quả học tập",
    fields: [
      ["number", "curricular_units_1st_sem_credited", "1st sem credited / Công nhận HK1", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_1st_sem_enrolled", "1st sem enrolled / Đăng ký HK1", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_1st_sem_evaluations", "1st sem evaluations / Đánh giá HK1", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_1st_sem_approved", "1st sem approved / Qua môn HK1", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_1st_sem_grade", "1st sem grade / Điểm TB HK1", { min: 0, max: 20, step: 0.1 }],
      ["number", "curricular_units_1st_sem_without_evaluations", "1st sem without evaluations / Không đánh giá HK1", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_2nd_sem_credited", "2nd sem credited / Công nhận HK2", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_2nd_sem_enrolled", "2nd sem enrolled / Đăng ký HK2", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_2nd_sem_evaluations", "2nd sem evaluations / Đánh giá HK2", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_2nd_sem_approved", "2nd sem approved / Qua môn HK2", { min: 0, max: 50, step: 1 }],
      ["number", "curricular_units_2nd_sem_grade", "2nd sem grade / Điểm TB HK2", { min: 0, max: 20, step: 0.1 }],
      ["number", "curricular_units_2nd_sem_without_evaluations", "2nd sem without evaluations / Không đánh giá HK2", { min: 0, max: 50, step: 1 }],
    ],
  },
  {
    title: "Economy / Kinh tế",
    fields: [
      ["number", "unemployment_rate", "Unemployment rate / Tỷ lệ thất nghiệp", { min: -10, max: 100, step: 0.1 }],
      ["number", "inflation_rate", "Inflation rate / Tỷ lệ lạm phát", { min: -20, max: 100, step: 0.1 }],
      ["number", "gdp", "GDP / Tăng trưởng GDP", { min: -100, max: 100, step: 0.1 }],
    ],
  },
];

function isYesNoOptions(mapping = {}) {
  return (
    Object.keys(mapping).length === 2 &&
    mapping[0] === "No / Không" &&
    mapping[1] === "Yes / Có"
  );
}

function normalizeOptions(mapping = {}, showCode = true) {
  return Object.entries(mapping)
    .map(([code, label]) => ({
      code: Number(code),
      label: showCode ? `${code} - ${label}` : label,
    }))
    .sort((a, b) => a.code - b.code);
}

function Field({ field, value, onChange, options }) {
  const [type, name, label, config] = field;

  if (type === "select" || type === "selectStatic") {
    const rawOptions = type === "select" ? options?.[config] : config;
    const showCode = !isYesNoOptions(rawOptions);
    const selectOptions = normalizeOptions(rawOptions, showCode);

    return (
      <label className="field">
        <span>{label}</span>
        <select value={value} onChange={(event) => onChange(name, Number(event.target.value))}>
          {selectOptions.map((option) => (
            <option key={option.code} value={option.code}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        min={config.min}
        max={config.max}
        step={config.step}
        onChange={(event) => onChange(name, Number(event.target.value))}
      />
    </label>
  );
}

function ResultCircle({ result }) {
  if (!result) return null;

  const percent = result.dropout_percent ?? 0;
  const color = result.color || (result.is_dropout ? "#ef4444" : "#22c55e");
  const statusText = result.is_dropout
    ? "Dropout / Có nguy cơ bỏ học"
    : "Graduate / Có khả năng tốt nghiệp";

  return (
    <section className="result-card">
      <div
        className="risk-circle"
        style={{
          "--value": `${Math.max(0, Math.min(100, percent))}%`,
          "--color": color,
        }}
      >
        <div className="circle-inner">
          <span className="circle-label">Dropout Risk</span>
          <strong>{percent.toFixed(2)}%</strong>
        </div>
      </div>

      <div className="result-text">
        <p className="status" style={{ color }}>
          {statusText}
        </p>
        <p>Risk level / Mức rủi ro: <b>{result.risk_level || "N/A"}</b></p>
      </div>
    </section>
  );
}

export default function App() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [options, setOptions] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/options`)
      .then((res) => res.json())
      .then(setOptions)
      .catch(() => setError("Không tải được options từ backend."));
  }, []);

  const isReady = useMemo(() => Object.keys(options).length > 0, [options]);

  function updateField(name, value) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Predict failed.");
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <h1>Dự đoán nguy cơ sinh viên bỏ học</h1>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="layout">
        <div className="form-panel">
          {!isReady && <p className="muted">Đang tải options...</p>}

          {sections.map((section) => (
            <section className="card" key={section.title}>
              <h2>{section.title}</h2>
              <div className="grid">
                {section.fields.map((field) => (
                  <Field
                    key={field[1]}
                    field={field}
                    value={form[field[1]]}
                    onChange={updateField}
                    options={options}
                  />
                ))}
              </div>
            </section>
          ))}

          <button className="predict-button" disabled={loading || !isReady}>
            {loading ? "Predicting..." : "Predict dropout risk / Dự đoán nguy cơ bỏ học"}
          </button>

          {error && <p className="error">{error}</p>}
        </div>

        <aside className="result-panel">
          <ResultCircle result={result} />
          {!result && (
            <div className="empty-result">
              <p>Nhập thông tin rồi bấm dự đoán.</p>
            </div>
          )}
        </aside>
      </form>
    </main>
  );
}
