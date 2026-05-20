from pathlib import Path

import joblib
import pandas as pd
import streamlit as st


# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="Student Dropout Risk Prediction | Dự đoán nguy cơ bỏ học",
    page_icon="🎓",
    layout="wide",
)


# =========================================================
# Feature engineering - phải giống notebook train model
# =========================================================
def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = (
        dataframe.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return dataframe


def add_engineered_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    eps = 1e-6

    dataframe["approval_rate_1st_sem"] = (
        dataframe["curricular_units_1st_sem_(approved)"] /
        (dataframe["curricular_units_1st_sem_(enrolled)"] + eps)
    )

    dataframe["approval_rate_2nd_sem"] = (
        dataframe["curricular_units_2nd_sem_(approved)"] /
        (dataframe["curricular_units_2nd_sem_(enrolled)"] + eps)
    )

    dataframe["total_approved_units"] = (
        dataframe["curricular_units_1st_sem_(approved)"] +
        dataframe["curricular_units_2nd_sem_(approved)"]
    )

    dataframe["total_enrolled_units"] = (
        dataframe["curricular_units_1st_sem_(enrolled)"] +
        dataframe["curricular_units_2nd_sem_(enrolled)"]
    )

    dataframe["overall_approval_rate"] = (
        dataframe["total_approved_units"] /
        (dataframe["total_enrolled_units"] + eps)
    )

    dataframe["grade_change"] = (
        dataframe["curricular_units_2nd_sem_(grade)"] -
        dataframe["curricular_units_1st_sem_(grade)"]
    )

    dataframe["avg_semester_grade"] = (
        dataframe["curricular_units_1st_sem_(grade)"] +
        dataframe["curricular_units_2nd_sem_(grade)"]
    ) / 2

    dataframe["financial_risk"] = (
        dataframe["debtor"].astype(int) +
        (1 - dataframe["tuition_fees_up_to_date"].astype(int))
    )

    return dataframe


# =========================================================
# Load checkpoint
# =========================================================
@st.cache_resource
def load_checkpoint_from_path(path: str):
    return joblib.load(path)


def predict_from_raw_input(raw_input_dict: dict, checkpoint: dict):
    # Notebook lưu final model trực tiếp ở key "model"
    # Giữ fallback "models" để app vẫn chạy nếu dùng checkpoint format cũ.
    real_model_name = checkpoint.get("best_model_name", "Unknown model")

    if "model" in checkpoint:
        model = checkpoint["model"]
    elif "models" in checkpoint and real_model_name in checkpoint["models"]:
        model = checkpoint["models"][real_model_name]
    else:
        raise KeyError(
            "Checkpoint không có key 'model'. "
            "Hãy dùng file models/best_model_Random_Forest.pkl được lưu từ notebook."
        )

    input_df = pd.DataFrame([raw_input_dict])
    input_df = normalize_columns(input_df)
    input_df = add_engineered_features(input_df)

    selected_raw_features = checkpoint["selected_raw_features"]

    missing_cols = [col for col in selected_raw_features if col not in input_df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns / Thiếu cột đầu vào: {missing_cols}")

    input_df = input_df[selected_raw_features].copy()

    # Notebook convert các selected features về numeric trước khi fit preprocessor.
    for col in selected_raw_features:
        input_df[col] = pd.to_numeric(input_df[col], errors="raise")

    processed = checkpoint["preprocessor"].transform(input_df)

    if hasattr(processed, "toarray"):
        processed = processed.toarray()

    input_processed = pd.DataFrame(
        processed,
        columns=checkpoint["processed_feature_names"],
    )

    pred = model.predict(input_processed)[0]
    try:
        pred_key = int(pred)
    except (TypeError, ValueError):
        pred_key = pred

    inverse_mapping = checkpoint.get(
        "inverse_target_mapping",
        {0: "Graduate", 1: "Dropout"}
    )

    prediction_label = inverse_mapping.get(
        pred_key,
        inverse_mapping.get(str(pred_key), str(pred_key))
    )

    dropout_probability = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(input_processed)[0]

        # Lấy đúng xác suất của class Dropout = 1, không giả định luôn nằm ở index 1.
        classes = list(getattr(model, "classes_", []))
        if 1 in classes:
            dropout_idx = classes.index(1)
        elif "Dropout" in classes:
            dropout_idx = classes.index("Dropout")
        else:
            dropout_idx = 1 if len(proba) > 1 else 0

        dropout_probability = float(proba[dropout_idx])

    return {
        "actual_model_used": real_model_name,
        "prediction": prediction_label,
        "dropout_probability": dropout_probability,
        "raw_features_used": input_df,
    }


# =========================================================
# Input helpers
# =========================================================
def select_code(label: str, mapping: dict[int, str], default_code: int, help_text: str | None = None) -> int:
    options = [f"{code} — {name}" for code, name in mapping.items()]
    codes = list(mapping.keys())

    if default_code in codes:
        default_index = codes.index(default_code)
    else:
        default_index = 0

    selected = st.selectbox(
        label,
        options,
        index=default_index,
        help=help_text,
    )

    return int(selected.split(" — ")[0])


def yes_no_select(label: str, default: int = 0, help_text: str | None = None) -> int:
    options = {
        "No / Không": 0,
        "Yes / Có": 1,
    }

    labels = list(options.keys())
    default_label = "Yes / Có" if default == 1 else "No / Không"

    selected = st.selectbox(
        label,
        labels,
        index=labels.index(default_label),
        help=help_text,
    )

    return options[selected]


def int_input(
    label: str,
    value: int,
    min_value: int = 0,
    max_value: int = 99999,
    help_text: str | None = None,
) -> int:
    return int(
        st.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=1,
            help=help_text,
        )
    )


def float_input(
    label: str,
    value: float,
    min_value: float = -100.0,
    max_value: float = 1000.0,
    step: float = 0.1,
    help_text: str | None = None,
) -> float:
    return float(
        st.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            step=step,
            help=help_text,
        )
    )


# =========================================================
# Result UI helper
# =========================================================
def render_dropout_circle(dropout_probability: float, is_dropout: bool, prediction_label: str, model_name: str):
    """Hiển thị một vòng tròn đơn giản thay cho biểu đồ pie."""
    percent = max(0.0, min(100.0, dropout_probability * 100.0))

    if is_dropout:
        main_color = "#ef4444"   # red
        soft_color = "rgba(239, 68, 68, 0.16)"
        status_text = "Dropout / Có nguy cơ bỏ học"
    else:
        main_color = "#22c55e"   # green
        soft_color = "rgba(34, 197, 94, 0.16)"
        status_text = "Graduate / Có khả năng tốt nghiệp"

    st.markdown(
        f"""
        <style>
        .result-card {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 28px 16px 18px 16px;
            border-radius: 22px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(15, 23, 42, 0.28);
            margin-top: 8px;
        }}

        .dropout-ring {{
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background:
                radial-gradient(circle at center, #0e1117 0 58%, transparent 59%),
                conic-gradient({main_color} {percent:.2f}%, rgba(148, 163, 184, 0.20) 0);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 32px {soft_color};
        }}

        .dropout-inner {{
            width: 176px;
            height: 176px;
            border-radius: 50%;
            background: #0e1117;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(148, 163, 184, 0.18);
        }}

        .dropout-value {{
            font-size: 42px;
            line-height: 1;
            font-weight: 800;
            color: {main_color};
            margin-bottom: 10px;
        }}

        .dropout-label {{
            font-size: 15px;
            font-weight: 650;
            color: rgba(226, 232, 240, 0.92);
            text-align: center;
        }}

        .result-status {{
            margin-top: 20px;
            padding: 9px 18px;
            border-radius: 999px;
            background: {soft_color};
            color: {main_color};
            font-size: 18px;
            font-weight: 750;
            text-align: center;
        }}

        .model-caption {{
            margin-top: 12px;
            color: rgba(148, 163, 184, 0.95);
            font-size: 13px;
            text-align: center;
        }}
        </style>

        <div class="result-card">
            <div class="dropout-ring">
                <div class="dropout-inner">
                    <div class="dropout-value">{percent:.2f}%</div>
                    <div class="dropout-label">Dropout risk<br/>Xác suất bỏ học</div>
                </div>
            </div>
            <div class="result-status">{status_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Code mappings from UCI dataset
# =========================================================
MARITAL_STATUS = {
    1: "Single / Độc thân",
    2: "Married / Đã kết hôn",
    3: "Widower / Góa vợ/chồng",
    4: "Divorced / Ly hôn",
    5: "Facto union / Sống chung như vợ chồng",
    6: "Legally separated / Ly thân hợp pháp",
}

APPLICATION_MODE = {
    1: "1st phase - general contingent / Đợt 1 - diện chung",
    2: "Ordinance No. 612/93",
    5: "1st phase - special contingent, Azores Island",
    7: "Holders of other higher courses / Đã có bằng/chương trình ĐH khác",
    10: "Ordinance No. 854-B/99",
    15: "International student, bachelor / Sinh viên quốc tế",
    16: "1st phase - special contingent, Madeira Island",
    17: "2nd phase - general contingent / Đợt 2 - diện chung",
    18: "3rd phase - general contingent / Đợt 3 - diện chung",
    26: "Ordinance No. 533-A/99, item b2",
    27: "Ordinance No. 533-A/99, item b3",
    39: "Over 23 years old / Trên 23 tuổi",
    42: "Transfer / Chuyển trường",
    43: "Change of course / Đổi ngành",
    44: "Technological specialization diploma holders",
    51: "Change of institution/course / Đổi trường hoặc đổi ngành",
    53: "Short cycle diploma holders",
    57: "Change of institution/course, international",
}

COURSE = {
    33: "Biofuel Production Technologies / Công nghệ sản xuất nhiên liệu sinh học",
    171: "Animation and Multimedia Design / Thiết kế hoạt hình & đa phương tiện",
    8014: "Social Service, evening attendance / Công tác xã hội - hệ tối",
    9003: "Agronomy / Nông học",
    9070: "Communication Design / Thiết kế truyền thông",
    9085: "Veterinary Nursing / Điều dưỡng thú y",
    9119: "Informatics Engineering / Kỹ thuật tin học",
    9130: "Equinculture / Chăn nuôi ngựa",
    9147: "Management / Quản trị",
    9238: "Social Service / Công tác xã hội",
    9254: "Tourism / Du lịch",
    9500: "Nursing / Điều dưỡng",
    9556: "Oral Hygiene / Vệ sinh răng miệng",
    9670: "Advertising and Marketing Management / Quảng cáo & marketing",
    9773: "Journalism and Communication / Báo chí & truyền thông",
    9853: "Basic Education / Giáo dục cơ bản",
    9991: "Management, evening attendance / Quản trị - hệ tối",
}

PREVIOUS_QUALIFICATION = {
    1: "Secondary education / THPT",
    2: "Higher education - bachelor's degree / Cử nhân",
    3: "Higher education - degree / Bằng ĐH",
    4: "Higher education - master's / Thạc sĩ",
    5: "Higher education - doctorate / Tiến sĩ",
    6: "Frequency of higher education / Từng học giáo dục ĐH",
    9: "12th year not completed / Lớp 12 chưa hoàn thành",
    10: "11th year not completed / Lớp 11 chưa hoàn thành",
    12: "Other - 11th year / Khác - lớp 11",
    14: "10th year / Lớp 10",
    15: "10th year not completed / Lớp 10 chưa hoàn thành",
    19: "Basic education 3rd cycle / Giáo dục cơ bản chu kỳ 3",
    38: "Basic education 2nd cycle / Giáo dục cơ bản chu kỳ 2",
    39: "Technological specialization course / Chuyên môn công nghệ",
    40: "Higher education - degree, 1st cycle / ĐH chu kỳ 1",
    42: "Professional higher technical course / Kỹ thuật chuyên nghiệp",
    43: "Higher education - master, 2nd cycle / Thạc sĩ chu kỳ 2",
}

NACIONALITY = {
    1: "Portuguese / Bồ Đào Nha",
    2: "German / Đức",
    6: "Spanish / Tây Ban Nha",
    11: "Italian / Ý",
    13: "Dutch / Hà Lan",
    14: "English / Anh",
    17: "Lithuanian / Litva",
    21: "Angolan / Angola",
    22: "Cape Verdean / Cabo Verde",
    24: "Guinean / Guinea",
    25: "Mozambican / Mozambique",
    26: "Santomean / São Tomé",
    32: "Turkish / Thổ Nhĩ Kỳ",
    41: "Brazilian / Brazil",
    62: "Romanian / Romania",
    100: "Moldova",
    101: "Mexican / Mexico",
    103: "Ukrainian / Ukraine",
    105: "Russian / Nga",
    108: "Cuban / Cuba",
    109: "Colombian / Colombia",
}

QUALIFICATION = {
    1: "Secondary Education - 12th Year / THPT",
    2: "Higher Education - Bachelor's Degree / Cử nhân",
    3: "Higher Education - Degree / Bằng ĐH",
    4: "Higher Education - Master's / Thạc sĩ",
    5: "Higher Education - Doctorate / Tiến sĩ",
    6: "Frequency of Higher Education / Từng học ĐH",
    9: "12th Year not completed / Lớp 12 chưa hoàn thành",
    10: "11th Year not completed / Lớp 11 chưa hoàn thành",
    11: "7th Year old system / Lớp 7 hệ cũ",
    12: "Other - 11th Year / Khác - lớp 11",
    13: "2nd year complementary high school course",
    14: "10th Year / Lớp 10",
    18: "General commerce course / Thương mại tổng quát",
    19: "Basic Education 3rd Cycle / Giáo dục cơ bản chu kỳ 3",
    20: "Complementary High School Course",
    22: "Technical-professional course / Trung cấp nghề",
    25: "Complementary High School Course not concluded",
    26: "7th year of schooling / Lớp 7",
    27: "2nd cycle general high school course",
    29: "9th Year not completed / Lớp 9 chưa hoàn thành",
    30: "8th year of schooling / Lớp 8",
    31: "General Course of Administration and Commerce",
    33: "Supplementary Accounting and Administration",
    34: "Unknown / Không rõ",
    35: "Can't read or write / Không biết đọc viết",
    36: "Can read without 4th year schooling / Biết đọc nhưng chưa học hết lớp 4",
    37: "Basic education 1st cycle / Giáo dục cơ bản chu kỳ 1",
    38: "Basic Education 2nd Cycle / Giáo dục cơ bản chu kỳ 2",
    39: "Technological specialization course / Chuyên môn công nghệ",
    40: "Higher education - degree, 1st cycle / ĐH chu kỳ 1",
    41: "Specialized higher studies course",
    42: "Professional higher technical course",
    43: "Higher Education - Master, 2nd cycle / Thạc sĩ chu kỳ 2",
    44: "Higher Education - Doctorate, 3rd cycle / Tiến sĩ chu kỳ 3",
}

MOTHER_OCCUPATION = {
    0: "Student / Sinh viên",
    1: "Directors and executive managers / Quản lý, điều hành",
    2: "Intellectual and scientific specialists / Chuyên gia trí thức, khoa học",
    3: "Intermediate level technicians / Kỹ thuật viên trung cấp",
    4: "Administrative staff / Nhân viên hành chính",
    5: "Services, security and sellers / Dịch vụ, an ninh, bán hàng",
    6: "Farmers and skilled agriculture workers / Nông nghiệp, thủy sản, lâm nghiệp",
    7: "Skilled industry and construction workers / Công nghiệp, xây dựng",
    8: "Machine operators and assembly workers / Vận hành máy, lắp ráp",
    9: "Unskilled workers / Lao động phổ thông",
    10: "Armed forces professions / Quân đội",
    90: "Other situation / Khác",
    99: "Blank / Không có thông tin",
    122: "Health professionals / Y tế",
    123: "Teachers / Giáo viên",
    125: "ICT specialists / Chuyên gia CNTT-TT",
    131: "Science and engineering technicians / Kỹ thuật viên khoa học, kỹ thuật",
    132: "Health technicians / Kỹ thuật viên y tế",
    134: "Legal, social, sports, cultural technicians",
    141: "Office workers and secretaries / Văn phòng, thư ký",
    143: "Accounting, statistics, finance operators",
    144: "Other administrative support staff",
    151: "Personal service workers / Dịch vụ cá nhân",
    152: "Sellers / Người bán hàng",
    153: "Personal care workers / Chăm sóc cá nhân",
    171: "Skilled construction workers / Công nhân xây dựng có tay nghề",
    173: "Printing, precision, jewelry, artisan workers",
    175: "Food, woodworking, clothing craft workers",
    191: "Cleaning workers / Lao công",
    192: "Unskilled agriculture/fishery/forestry workers",
    193: "Unskilled industry/construction/transport workers",
    194: "Meal preparation assistants / Phụ bếp",
}

FATHER_OCCUPATION = {
    0: "Student / Sinh viên",
    1: "Directors and executive managers / Quản lý, điều hành",
    2: "Intellectual and scientific specialists / Chuyên gia trí thức, khoa học",
    3: "Intermediate level technicians / Kỹ thuật viên trung cấp",
    4: "Administrative staff / Nhân viên hành chính",
    5: "Services, security and sellers / Dịch vụ, an ninh, bán hàng",
    6: "Farmers and skilled agriculture workers / Nông nghiệp, thủy sản, lâm nghiệp",
    7: "Skilled industry and construction workers / Công nghiệp, xây dựng",
    8: "Machine operators and assembly workers / Vận hành máy, lắp ráp",
    9: "Unskilled workers / Lao động phổ thông",
    10: "Armed forces professions / Quân đội",
    90: "Other situation / Khác",
    99: "Blank / Không có thông tin",
    101: "Armed Forces Officers / Sĩ quan quân đội",
    102: "Armed Forces Sergeants / Hạ sĩ quan quân đội",
    103: "Other Armed Forces personnel / Nhân sự quân đội khác",
    112: "Administrative and commercial service directors",
    114: "Hotel, catering, trade and service directors",
    121: "Physical sciences, math, engineering specialists",
    122: "Health professionals / Y tế",
    123: "Teachers / Giáo viên",
    124: "Finance, accounting, admin, PR specialists",
    131: "Science and engineering technicians",
    132: "Health technicians / Kỹ thuật viên y tế",
    134: "Legal, social, sports, cultural technicians",
    135: "ICT technicians / Kỹ thuật viên CNTT-TT",
    141: "Office workers and secretaries / Văn phòng, thư ký",
    143: "Accounting, statistics, finance operators",
    144: "Other administrative support staff",
    151: "Personal service workers / Dịch vụ cá nhân",
    152: "Sellers / Người bán hàng",
    153: "Personal care workers / Chăm sóc cá nhân",
    154: "Protection and security services / Bảo vệ, an ninh",
    161: "Market-oriented farmers and animal production workers",
    163: "Subsistence farmers, fishermen, hunters",
    171: "Skilled construction workers",
    172: "Metalworking skilled workers",
    174: "Electricity and electronics skilled workers",
    175: "Food, woodworking, clothing craft workers",
    181: "Fixed plant and machine operators",
    182: "Assembly workers / Công nhân lắp ráp",
    183: "Vehicle drivers and mobile equipment operators",
    192: "Unskilled agriculture/fishery/forestry workers",
    193: "Unskilled industry/construction/transport workers",
    194: "Meal preparation assistants / Phụ bếp",
    195: "Street vendors and street service providers",
}


# =========================================================
# UI
# =========================================================
st.title("🎓 Student Dropout Risk Prediction")
st.subheader("Dự đoán nguy cơ sinh viên bỏ học")

# Notebook lưu file theo dạng: models/best_model_<Tên_model>.pkl
default_checkpoint_path = Path("models/best_model_Random_Forest.pkl")

if not default_checkpoint_path.exists():
    # Fallback: tự tìm checkpoint best_model_*.pkl trong thư mục models
    candidates = sorted(Path("models").glob("best_model_*.pkl"))
    if candidates:
        default_checkpoint_path = candidates[0]

if default_checkpoint_path.exists():
    checkpoint = load_checkpoint_from_path(str(default_checkpoint_path))
    st.caption(f"Loaded checkpoint / Đã tải checkpoint: `{default_checkpoint_path}`")
else:
    st.error(
        "Không tìm thấy checkpoint. "
        "Hãy chạy notebook đến cell SAVE FINAL CHECKPOINT rồi đặt file "
        "`best_model_Random_Forest.pkl` trong thư mục `models/`."
    )
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Admission / Tuyển sinh",
    "2. Student profile / Hồ sơ",
    "3. Academic results / Kết quả học tập",
    "4. Economy / Kinh tế",
])


with tab1:
    col1, col2 = st.columns(2)

    with col1:
        marital_status = select_code(
            "Marital status / Tình trạng hôn nhân",
            MARITAL_STATUS,
            default_code=1,
        )

        application_mode = select_code(
            "Application mode / Hình thức nhập học",
            APPLICATION_MODE,
            default_code=1,
        )

        application_order = int_input(
            "Application order / Thứ tự nguyện vọng",
            value=1,
            min_value=0,
            max_value=9,
            help_text="0 = first choice / nguyện vọng đầu tiên; 9 = last choice / nguyện vọng cuối.",
        )

        course = select_code(
            "Course / Ngành học",
            COURSE,
            default_code=9238,
        )

        daytime_evening_attendance = st.selectbox(
            "Daytime/evening attendance / Hệ học",
            ["Daytime / Ban ngày", "Evening / Buổi tối"],
            index=0,
        )
        daytime_evening_attendance = 1 if daytime_evening_attendance.startswith("Daytime") else 0

    with col2:
        previous_qualification = select_code(
            "Previous qualification / Văn bằng trước đó",
            PREVIOUS_QUALIFICATION,
            default_code=1,
        )

        previous_qualification_grade = float_input(
            "Previous qualification grade / Điểm văn bằng trước đó",
            value=120.0,
            min_value=0.0,
            max_value=200.0,
        )

        admission_grade = float_input(
            "Admission grade / Điểm đầu vào",
            value=120.0,
            min_value=0.0,
            max_value=200.0,
        )

        nacionality = select_code(
            "Nationality / Quốc tịch",
            NACIONALITY,
            default_code=1,
        )


with tab2:
    col1, col2 = st.columns(2)

    with col1:
        gender_label = st.selectbox(
            "Gender / Giới tính",
            ["Female / Nữ", "Male / Nam"],
            index=0,
        )
        gender = 0 if gender_label.startswith("Female") else 1

        age_at_enrollment = int_input(
            "Age at enrollment / Tuổi khi nhập học",
            value=20,
            min_value=15,
            max_value=80,
        )

        displaced = yes_no_select(
            "Displaced / Sinh viên xa nhà hoặc di chuyển nơi ở?",
            default=0,
        )

        educational_special_needs = yes_no_select(
            "Educational special needs / Có nhu cầu giáo dục đặc biệt?",
            default=0,
        )

        international = yes_no_select(
            "International / Sinh viên quốc tế?",
            default=0,
        )

    with col2:
        mothers_qualification = select_code(
            "Mother's qualification / Trình độ học vấn của mẹ",
            QUALIFICATION,
            default_code=1,
        )

        fathers_qualification = select_code(
            "Father's qualification / Trình độ học vấn của bố",
            QUALIFICATION,
            default_code=1,
        )

        mothers_occupation = select_code(
            "Mother's occupation / Nghề nghiệp của mẹ",
            MOTHER_OCCUPATION,
            default_code=4,
        )

        fathers_occupation = select_code(
            "Father's occupation / Nghề nghiệp của bố",
            FATHER_OCCUPATION,
            default_code=4,
        )

    st.markdown("### Financial status / Tài chính")
    col3, col4, col5 = st.columns(3)

    with col3:
        debtor = yes_no_select(
            "Debtor / Đang nợ học phí hoặc khoản phí?",
            default=0,
        )

    with col4:
        tuition_fees_up_to_date = yes_no_select(
            "Tuition fees up to date / Đã đóng học phí đúng hạn?",
            default=1,
        )

    with col5:
        scholarship_holder = yes_no_select(
            "Scholarship holder / Có học bổng?",
            default=0,
        )


with tab3:
    st.markdown("### 1st semester / Học kỳ 1")
    col1, col2, col3 = st.columns(3)

    with col1:
        cu_1_credited = float_input(
            "1st sem credited / Số học phần được công nhận HK1",
            value=0.0,
            min_value=0.0,
            max_value=50.0,
        )

        cu_1_enrolled = float_input(
            "1st sem enrolled / Số học phần đăng ký HK1",
            value=6.0,
            min_value=0.0,
            max_value=50.0,
        )

    with col2:
        cu_1_evaluations = float_input(
            "1st sem evaluations / Số học phần được đánh giá HK1",
            value=6.0,
            min_value=0.0,
            max_value=50.0,
        )

        cu_1_approved = float_input(
            "1st sem approved / Số học phần qua môn HK1",
            value=5.0,
            min_value=0.0,
            max_value=50.0,
        )

    with col3:
        cu_1_grade = float_input(
            "1st sem grade / Điểm trung bình HK1",
            value=12.0,
            min_value=0.0,
            max_value=20.0,
        )

        cu_1_without_evaluations = float_input(
            "1st sem without evaluations / Số học phần không được đánh giá HK1",
            value=0.0,
            min_value=0.0,
            max_value=50.0,
        )

    st.markdown("### 2nd semester / Học kỳ 2")
    col4, col5, col6 = st.columns(3)

    with col4:
        cu_2_credited = float_input(
            "2nd sem credited / Số học phần được công nhận HK2",
            value=0.0,
            min_value=0.0,
            max_value=50.0,
        )

        cu_2_enrolled = float_input(
            "2nd sem enrolled / Số học phần đăng ký HK2",
            value=6.0,
            min_value=0.0,
            max_value=50.0,
        )

    with col5:
        cu_2_evaluations = float_input(
            "2nd sem evaluations / Số học phần được đánh giá HK2",
            value=6.0,
            min_value=0.0,
            max_value=50.0,
        )

        cu_2_approved = float_input(
            "2nd sem approved / Số học phần qua môn HK2",
            value=5.0,
            min_value=0.0,
            max_value=50.0,
        )

    with col6:
        cu_2_grade = float_input(
            "2nd sem grade / Điểm trung bình HK2",
            value=12.0,
            min_value=0.0,
            max_value=20.0,
        )

        cu_2_without_evaluations = float_input(
            "2nd sem without evaluations / Số học phần không được đánh giá HK2",
            value=0.0,
            min_value=0.0,
            max_value=50.0,
        )


with tab4:
    col1, col2, col3 = st.columns(3)

    with col1:
        unemployment_rate = float_input(
            "Unemployment rate / Tỷ lệ thất nghiệp",
            value=10.0,
            min_value=-10.0,
            max_value=100.0,
        )

    with col2:
        inflation_rate = float_input(
            "Inflation rate / Tỷ lệ lạm phát",
            value=1.0,
            min_value=-20.0,
            max_value=100.0,
        )

    with col3:
        gdp = float_input(
            "GDP / Tăng trưởng GDP",
            value=1.0,
            min_value=-100.0,
            max_value=100.0,
        )


# =========================================================
# Build raw input
# Tên key để dạng gần với dataset, sau đó normalize_columns sẽ đổi giống notebook
# =========================================================
raw_input = {
    "marital_status": marital_status,
    "application_mode": application_mode,
    "application_order": application_order,
    "course": course,
    "daytime/evening_attendance": daytime_evening_attendance,
    "previous_qualification": previous_qualification,
    "previous_qualification_(grade)": previous_qualification_grade,
    "nacionality": nacionality,
    "mother's_qualification": mothers_qualification,
    "father's_qualification": fathers_qualification,
    "mother's_occupation": mothers_occupation,
    "father's_occupation": fathers_occupation,
    "admission_grade": admission_grade,
    "displaced": displaced,
    "educational_special_needs": educational_special_needs,
    "debtor": debtor,
    "tuition_fees_up_to_date": tuition_fees_up_to_date,
    "gender": gender,
    "scholarship_holder": scholarship_holder,
    "age_at_enrollment": age_at_enrollment,
    "international": international,
    "curricular_units_1st_sem_(credited)": cu_1_credited,
    "curricular_units_1st_sem_(enrolled)": cu_1_enrolled,
    "curricular_units_1st_sem_(evaluations)": cu_1_evaluations,
    "curricular_units_1st_sem_(approved)": cu_1_approved,
    "curricular_units_1st_sem_(grade)": cu_1_grade,
    "curricular_units_1st_sem_(without_evaluations)": cu_1_without_evaluations,
    "curricular_units_2nd_sem_(credited)": cu_2_credited,
    "curricular_units_2nd_sem_(enrolled)": cu_2_enrolled,
    "curricular_units_2nd_sem_(evaluations)": cu_2_evaluations,
    "curricular_units_2nd_sem_(approved)": cu_2_approved,
    "curricular_units_2nd_sem_(grade)": cu_2_grade,
    "curricular_units_2nd_sem_(without_evaluations)": cu_2_without_evaluations,
    "unemployment_rate": unemployment_rate,
    "inflation_rate": inflation_rate,
    "gdp": gdp,
}


st.divider()

if st.button("Predict dropout risk / Dự đoán nguy cơ bỏ học", type="primary"):
    try:
        result = predict_from_raw_input(raw_input, checkpoint)

        prediction = str(result["prediction"])
        prob = result["dropout_probability"]
        is_dropout = prediction.strip().lower() == "dropout"

        if prob is None:
            st.info(
                "This model does not provide probability / "
                "Mô hình này không hỗ trợ xác suất."
            )
        else:
            st.markdown("## Prediction result / Kết quả dự đoán")
            render_dropout_circle(
                dropout_probability=prob,
                is_dropout=is_dropout,
                prediction_label=prediction,
                model_name=result["actual_model_used"],
            )

    except Exception as e:
        st.exception(e)
