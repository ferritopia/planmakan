import os
import streamlit as st
from dotenv import dotenv_values
from groq import Groq
from datetime import datetime
import json

# Configure page settings
st.set_page_config(
    page_title="Planmakan - MealPlan Buddy",
    page_icon="🍽️",
    layout="wide"
)

# Initialize environment variables
try:
    secrets = dotenv_values(".env")  # for dev env
    GROQ_API_KEY = secrets["GROQ_API_KEY"]
except:
    secrets = st.secrets  # for streamlit deployment
    GROQ_API_KEY = secrets["GROQ_API_KEY"]

# Save the API key to environment variable
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Initialize Groq client
client = Groq()

# Function to parse Groq stream
def parse_groq_stream(stream):
    response = ""
    for chunk in stream:
        if chunk.choices:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                response += content
                yield content
    return response

# Cache decorator for storing mealplan results
@st.cache_data
def generate_mealplan(user_data):
    messages = [
        {
            "role": "system",
            "content": """Anda adalah seorang ahli gizi profesional dna mealplanner, berikan analisa singkat kebutuhan dan tujuan, lalu buatkan mealplan untuk user berdasarkan data yang ada, lalu buat mealplan berdasarkan periode yang diminta, dan tampilkan dalam bentuk tabel, di dalamnya juga terdapat informasi seperti kalori, karbo, protein, lemak untuk setiap makanannya """
        },
        {
            "role": "user",
            "content": f"Tolong buat rencana makan berdasarkan data pengguna ini: {json.dumps(user_data, indent=2)}"
        }
    ]
    
    stream = client.chat.completions.create(
        model="llama-3.2-1b-preview",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        stream=True
    )
    
    return "".join(list(parse_groq_stream(stream)))

# ... (kode sebelumnya tetap sama sampai fungsi generate_mealplan)

# Tambahkan fungsi baru untuk generate meal prep
@st.cache_data
def generate_meal_prep(user_data, meal_plan):
    messages = [
        {
            "role": "system",
            "content": """Anda adalah seorang koki profesional dan ahli persiapan makanan. Berdasarkan rencana makan pengguna, buatlah panduan persiapan makanan yang terperinci yang mencakup:
1. Daftar belanja untuk bahan-bahan
2. Langkah-langkah persiapan untuk setiap makanan
3. Instruksi penyimpanan dan tips
4. Teknik menghemat waktu
5. Instruksi memasak dengan perkiraan waktu persiapan
6. Alat dan peralatan yang dibutuhkan

Formatlah respons dalam bagian yang jelas dengan format markdown untuk meningkatkan keterbacaan. Pertimbangkan preferensi memasak pengguna, batasan anggaran, dan ketersediaan waktu."""
        },
        {
            "role": "user",
            "content": f"""Tolong buat panduan persiapan makanan berdasarkan data pengguna dan meal plan ini:
            User Data: {json.dumps(user_data, indent=2)}
            Meal Plan: {meal_plan}"""
        }
    ]
    
    stream = client.chat.completions.create(
        model="llama-3.2-1b-preview",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
        stream=True
    )
    
    return "".join(list(parse_groq_stream(stream)))

# ... (kode lain tetap sama sampai bagian Meal Prep Page)

# Function to calculate BMI
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return weight / (height_m * height_m)

# Initialize session state for navigation
if 'page' not in st.session_state:
    st.session_state.page = 'user_details'

if 'user_data' not in st.session_state:
    st.session_state.user_data = {}

# Sidebar navigation
st.sidebar.title("Navigation")
pages = {
    'user_details': '👤 Data',
    'meal_plan': '🍽️ Meal Plan',
    'meal_prep': '👩‍🍳 Meal Prep',
    'share': '📤 Share'
}

st.session_state.page = st.sidebar.radio("Go to", list(pages.values()))

# User Details Page
if st.session_state.page == '👤 Masukkan Data Anda':
    st.title("Personal Details")
    
    with st.form("user_details_form"):
        # Basic Information
        st.header("Basic Information")
        name = st.text_input("Nama", value=st.session_state.user_data.get('name', ''))
        weight = st.number_input("Berat badan (kg)", min_value=30.0, max_value=200.0, value=float(st.session_state.user_data.get('weight', 70.0)))
        height = st.number_input("Tinggi (cm)", min_value=100.0, max_value=250.0, value=float(st.session_state.user_data.get('height', 170.0)))
        fat_percentage = st.number_input("Persentase lemak (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.user_data.get('fat_percentage', 20.0)))
        target_weight = st.number_input("Target berat badan (kg)", min_value=30.0, max_value=200.0, value=float(st.session_state.user_data.get('target_weight', 65.0)))
        
        # Activity Level
        activity_options = {
            "Sangat Aktif": "Latihan di gym 5-7 kali seminggu, dll.",
            "Aktif": "Latihan di gym 2-4 kali seminggu, dll.",
            "Moderat Aktif": "Latihan ringan 2-3 kali seminggu, dll.",
            "Rasanya Kurang Aktif": "Tidak terlalu rutin berlatih, dll.",
            "Tidak Aktif": "Sangat sedikit aktivitas fisik"
        }
        activity = st.selectbox("Level Aktivitas", 
                              options=list(activity_options.keys()),
                              format_func=lambda x: f"{x} - {activity_options[x][:30]}...",
                              index=list(activity_options.keys()).index(st.session_state.user_data.get('activity', 'Moderat Aktif')))

        # Diet Information
        st.header("Informasi Diet")
        diet_preferences = st.selectbox("Pilihan diet",
                                      ["Bebas", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Halal"],
                                      index=["Bebas", "Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Halal"].index(st.session_state.user_data.get('diet_preferences', 'Bebas')))
        
        liked_foods = st.text_area("Makanan yang Anda sukai", value=st.session_state.user_data.get('liked_foods', ''))
        disliked_foods = st.text_area("Makanan yang Anda tidak sukai", value=st.session_state.user_data.get('disliked_foods', ''))
        
        has_allergies = st.radio("Apakah Anda memiliki alergi makanan?", 
                               ['Tidak', 'Ya'],
                               index=['Tidak', 'Ya'].index(st.session_state.user_data.get('has_allergies', 'Tidak')))
        
        food_allergies = ''
        if has_allergies == 'Ya':
            food_allergies = st.text_area("Sebutkan alergi makanan Anda", value=st.session_state.user_data.get('food_allergies', ''))

        cuisine_preference = st.selectbox("Pilih menu makanan",
                                        ["Indonesia", "Jawa", "Chinese food", "Fusi Asia"],
                                        index=["Indonesia", "Jawa", "Chinese food", "Fusi Asia"].index(st.session_state.user_data.get('cuisine_preference', 'Indonesia')))

        meal_times = st.multiselect("Waktu makan yang diinginkan",
                                  ['Sarapan', 'Makan Siang', 'Makan Malam', 'Sebelum Tidur', 'Snack'],
                                  default=st.session_state.user_data.get('meal_times', ['Sarapan', 'Makan Siang', 'Makan Malam']))

        food_source = st.radio("Sumber makanan",
                             ['Memasak Sendiri', 'Beli'],
                             index=['Memasak Sendiri', 'Beli'].index(st.session_state.user_data.get('food_source', 'Memasak Sendiri')))

        budget_strict = st.radio("Apakah Anda memiliki anggaran yang ketat untuk belanja?",
                               ['Ya', 'Tidak'],
                               index=['Ya', 'Tidak'].index(st.session_state.user_data.get('budget_strict', 'Tidak')))

      # Tambahkan pilihan periode meal plan
        meal_plan_period = st.selectbox("Pilih periode meal plan yang diinginkan",
                                      ["Harian", "Mingguan", "Bulanan"],
                                      index=["Harian", "Mingguan", "Bulanan"].index(st.session_state.user_data.get('meal_plan_period', 'Harian')))

        submitted = st.form_submit_button("Simpan")

        if submitted:
            # Calculate BMI
            bmi = calculate_bmi(weight, height)
            
            # Save all data to session state
            st.session_state.user_data = {
                'name': name,
                'weight': weight,
                'height': height,
                'fat_percentage': fat_percentage,
                'target_weight': target_weight,
                'activity': activity,
                'bmi': bmi,
                'diet_preferences': diet_preferences,
                'liked_foods': liked_foods,
                'disliked_foods': disliked_foods,
                'has_allergies': has_allergies,
                'food_allergies': food_allergies,
                'cuisine_preference': cuisine_preference,
                'meal_times': meal_times,
                'food_source': food_source,
                'budget_strict': budget_strict,
                'meal_plan_period': meal_plan_period
            }
            
            st.success("Data berhasil disimpan!")

# Meal Plan Page
elif st.session_state.page == '🍽️ Meal Plan':
    if not st.session_state.user_data:
        st.warning("Silakan isi informasi mu terlebih dahulu.")
    else:
        st.title(f"Selamat {datetime.now().strftime('%A')}, {st.session_state.user_data['name']} 👋")
        
        if st.button("Buat Meal Plan"):
            with st.spinner("Generating your meal plan..."):
                meal_plan = generate_mealplan(st.session_state.user_data)
                st.session_state.current_meal_plan = meal_plan
                
            st.markdown("### Analisis")
            st.write(meal_plan)

# Modifikasi Meal Prep Page
elif st.session_state.page == '👩‍🍳 Meal Prep':
    st.title("Panduan Meal Prep")
    
    if not st.session_state.get('current_meal_plan'):
        st.warning("Silakan generate meal plan terlebih dahulu.")
    else:
        # Tampilkan meal plan yang sudah ada
        st.subheader("Meal Plan Anda")
        with st.expander("Lihat Meal Plan"):
            st.write(st.session_state.current_meal_plan)
        
        # Tombol untuk generate meal prep
        if 'meal_prep' not in st.session_state:
            if st.button("Buat Panduan Meal Prep"):
                with st.spinner("Membuat panduan meal prep..."):
                    meal_prep = generate_meal_prep(
                        st.session_state.user_data,
                        st.session_state.current_meal_plan
                    )
                    st.session_state.meal_prep = meal_prep
        
        # Tampilkan hasil meal prep jika sudah di-generate
        if 'meal_prep' in st.session_state:
            st.markdown("### Panduan Lengkap Meal Prep")
            st.markdown(st.session_state.meal_prep)
            
            # Tombol untuk generate ulang
            if st.button("Generate Ulang Meal Prep"):
                with st.spinner("Membuat ulang panduan meal prep..."):
                    meal_prep = generate_meal_prep(
                        st.session_state.user_data,
                        st.session_state.current_meal_plan
                    )
                    st.session_state.meal_prep = meal_prep

# ... (kode selanjutnya tetap sama)

# Share Page
elif st.session_state.page == '📤 Share':
    st.title("Bagikan Meal Plan")
    
    if not st.session_state.get('current_meal_plan'):
        st.warning("Silakan generate meal plan terlebih dahulu.")
    else:
        email = st.text_input("Masukkan alamat email")
        if st.button("Kirim"):
            st.success(f"Meal plan telah dikirim ke {email}")

if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made by Ferri")