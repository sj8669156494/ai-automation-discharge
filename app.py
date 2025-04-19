import streamlit as st
import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
import requests
from fpdf import FPDF
import io
import os

# Configuration
st.set_page_config(page_title="AI Discharge Summary Generator", layout="wide")

# API key setup - In production, use environment variables instead
MISTRAL_API_KEY = "aiV4QCxDyZQ4RExVOd65BwnMrbSsNK1Y"


# Function to generate synthetic patient data
def generate_synthetic_patient():
    first_names = ["John", "Jane", "Robert", "Maria", "David", "Sarah", "Michael", "Emma", "James", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                  "Martinez"]

    medications = [
        "Lisinopril 10mg", "Atorvastatin 20mg", "Metformin 500mg", "Levothyroxine 50mcg",
        "Amlodipine 5mg", "Metoprolol 25mg", "Omeprazole 20mg", "Albuterol inhaler",
        "Hydrochlorothiazide 12.5mg", "Gabapentin 300mg"
    ]

    diagnoses = [
        "Type 2 Diabetes", "Hypertension", "Hyperlipidemia", "Asthma", "COPD",
        "Coronary Artery Disease", "Heart Failure", "Atrial Fibrillation",
        "Osteoarthritis", "Chronic Kidney Disease"
    ]

    procedures = [
        "Coronary Angiography", "Appendectomy", "Cholecystectomy", "Total Knee Replacement",
        "Hip Replacement", "Colonoscopy", "CABG", "Hernia Repair", "Cataract Surgery", "None"
    ]

    vital_signs = {
        "temperature": round(random.uniform(97.0, 99.5), 1),
        "heart_rate": random.randint(60, 100),
        "blood_pressure_systolic": random.randint(110, 140),
        "blood_pressure_diastolic": random.randint(60, 90),
        "respiratory_rate": random.randint(12, 20),
        "oxygen_saturation": random.randint(95, 100)
    }

    lab_results = {
        "hemoglobin": round(random.uniform(12.0, 17.0), 1),
        "white_blood_cells": round(random.uniform(4.0, 11.0), 1),
        "platelets": random.randint(150, 450),
        "sodium": random.randint(135, 145),
        "potassium": round(random.uniform(3.5, 5.0), 1),
        "creatinine": round(random.uniform(0.6, 1.2), 1),
        "glucose": random.randint(70, 110)
    }

    # Generate random patient data
    dob = datetime.now() - timedelta(days=random.randint(18 * 365, 90 * 365))
    admission_date = datetime.now() - timedelta(days=random.randint(3, 14))
    discharge_date = datetime.now()

    # Generate a list of 1-3 random diagnoses
    patient_diagnoses = random.sample(diagnoses, random.randint(1, 3))
    # Generate a list of 1-4 random medications
    patient_medications = random.sample(medications, random.randint(1, 4))
    # Choose a random procedure or none
    patient_procedure = random.choice(procedures)

    patient = {
        "patient_info": {
            "first_name": random.choice(first_names),
            "last_name": random.choice(last_names),
            "date_of_birth": dob.strftime("%Y-%m-%d"),
            "gender": random.choice(["Male", "Female"]),
            "mrn": f"MRN{random.randint(100000, 999999)}",
        },
        "admission_info": {
            "admission_date": admission_date.strftime("%Y-%m-%d"),
            "discharge_date": discharge_date.strftime("%Y-%m-%d"),
            "length_of_stay": (discharge_date - admission_date).days,
            "attending_physician": f"Dr. {random.choice(last_names)}",
        },
        "clinical_info": {
            "diagnoses": patient_diagnoses,
            "procedures": patient_procedure,
            "medications": patient_medications,
            "allergies": random.choice(["No known allergies", "Penicillin", "Sulfa drugs", "Shellfish", "Latex"]),
        },
        "vital_signs": vital_signs,
        "laboratory_results": lab_results,
        "follow_up": {
            "appointment": (discharge_date + timedelta(days=random.randint(7, 21))).strftime("%Y-%m-%d"),
            "care_instructions": "Standard follow-up care",
        }
    }

    return patient


# Function to call Mistral API
def generate_discharge_summary(patient_data):
    url = "https://api.mistral.ai/v1/chat/completions"

    prompt = f"""
    Generate a comprehensive medical discharge summary based on the following patient data:

    {json.dumps(patient_data, indent=2)}

    Include the following sections:
    1. Patient Demographics
    2. Admission Information
    3. Hospital Course
    4. Discharge Diagnoses
    5. Procedures Performed
    6. Discharge Medications
    7. Follow-up Instructions
    8. Discharge Condition

    The summary should be professionally written as a medical document, using appropriate medical terminology.
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }

    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        summary = result["choices"][0]["message"]["content"]
        return summary
    except Exception as e:
        st.error(f"Error generating discharge summary: {str(e)}")
        return "Error generating discharge summary. Please try again."


# Function to generate PDF
def generate_pdf(patient_data, summary_text):
    pdf = FPDF()
    pdf.add_page()

    # Set up the document
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "DISCHARGE SUMMARY", 0, 1, "C")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Patient Information", 0, 1, "L")
    pdf.set_font("Arial", "", 10)

    patient_info = patient_data["patient_info"]
    pdf.cell(190, 6, f"Name: {patient_info['first_name']} {patient_info['last_name']}", 0, 1)
    pdf.cell(190, 6, f"DOB: {patient_info['date_of_birth']}", 0, 1)
    pdf.cell(190, 6, f"MRN: {patient_info['mrn']}", 0, 1)
    pdf.cell(190, 6, f"Gender: {patient_info['gender']}", 0, 1)

    admission_info = patient_data["admission_info"]
    pdf.cell(190, 6, f"Admission Date: {admission_info['admission_date']}", 0, 1)
    pdf.cell(190, 6, f"Discharge Date: {admission_info['discharge_date']}", 0, 1)
    pdf.cell(190, 6, f"Attending Physician: {admission_info['attending_physician']}", 0, 1)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Discharge Summary", 0, 1, "L")

    pdf.set_font("Arial", "", 10)

    # Add the summary text
    # Split the text into lines to avoid overflowing
    lines = summary_text.split('\n')
    for line in lines:
        # Handle multi-line paragraphs by wrapping text
        if len(line) > 0:
            pdf.multi_cell(190, 5, line)
        else:
            pdf.ln(5)  # Empty line

    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 10, "This is an AI-generated discharge summary and requires physician review.", 0, 1, "L")

    return pdf.output(dest='S').encode('latin1')


# UI Components
st.title("AI-Powered Discharge Summary Generator")

with st.sidebar:
    st.header("1. Patient Data")
    data_option = st.radio("Choose Data Source", ["Generate Synthetic Data", "Upload JSON/CSV", "Manual Entry"])

    if data_option == "Generate Synthetic Data":
        if st.button("Generate New Patient"):
            st.session_state.patient_data = generate_synthetic_patient()

    elif data_option == "Upload JSON/CSV":
        uploaded_file = st.file_uploader("Upload patient data", type=["json", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.json'):
                    patient_data = json.load(uploaded_file)
                    st.session_state.patient_data = patient_data
                elif uploaded_file.name.endswith('.csv'):
                    # This is a simplified approach - would need more processing for real CSV
                    df = pd.read_csv(uploaded_file)
                    patient_data = df.to_dict(orient='records')[0]
                    st.session_state.patient_data = patient_data
                st.success("Data loaded successfully")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

    elif data_option == "Manual Entry":
        st.write("Enter patient information manually:")
        # This would be expanded in a real application with many more fields
        first_name = st.text_input("First Name", "John")
        last_name = st.text_input("Last Name", "Doe")
        dob = st.date_input("Date of Birth", datetime.now() - timedelta(days=365 * 50))
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        mrn = st.text_input("MRN", "MRN123456")

        admission_date = st.date_input("Admission Date", datetime.now() - timedelta(days=7))
        discharge_date = st.date_input("Discharge Date", datetime.now())
        attending = st.text_input("Attending Physician", "Dr. Smith")

        diagnoses = st.text_area("Diagnoses (one per line)", "Hypertension\nType 2 Diabetes")

        if st.button("Save Patient Data"):
            patient_data = {
                "patient_info": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_of_birth": dob.strftime("%Y-%m-%d"),
                    "gender": gender,
                    "mrn": mrn,
                },
                "admission_info": {
                    "admission_date": admission_date.strftime("%Y-%m-%d"),
                    "discharge_date": discharge_date.strftime("%Y-%m-%d"),
                    "length_of_stay": (discharge_date - admission_date).days,
                    "attending_physician": attending,
                },
                "clinical_info": {
                    "diagnoses": diagnoses.split("\n"),
                    "procedures": "None",
                    "medications": ["None"],
                    "allergies": "No known allergies",
                }
            }
            st.session_state.patient_data = patient_data
            st.success("Patient data saved")

# Initialize session state variables if they don't exist
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = generate_synthetic_patient()
if 'discharge_summary' not in st.session_state:
    st.session_state.discharge_summary = ""

# Main content area
st.header("2. Patient Data Preview")

if st.session_state.patient_data:
    col1, col2 = st.columns(2)

    with col1:
        patient_info = st.session_state.patient_data["patient_info"]
        st.subheader("Patient Information")
        st.write(f"**Name**: {patient_info['first_name']} {patient_info['last_name']}")
        st.write(f"**DOB**: {patient_info['date_of_birth']}")
        st.write(f"**MRN**: {patient_info['mrn']}")
        st.write(f"**Gender**: {patient_info['gender']}")

    with col2:
        admission_info = st.session_state.patient_data["admission_info"]
        st.subheader("Admission Information")
        st.write(f"**Admission Date**: {admission_info['admission_date']}")
        st.write(f"**Discharge Date**: {admission_info['discharge_date']}")
        st.write(f"**Length of Stay**: {admission_info['length_of_stay']} days")
        st.write(f"**Attending Physician**: {admission_info['attending_physician']}")

    st.subheader("Clinical Information")
    if "clinical_info" in st.session_state.patient_data:
        clinical_info = st.session_state.patient_data["clinical_info"]
        st.write(f"**Diagnoses**: {', '.join(clinical_info['diagnoses'])}")
        st.write(f"**Procedures**: {clinical_info['procedures']}")
        st.write(f"**Medications**: {', '.join(clinical_info['medications'])}")
        st.write(f"**Allergies**: {clinical_info['allergies']}")

    # Generate discharge summary button
    if st.button("Generate Discharge Summary"):
        with st.spinner("Generating discharge summary..."):
            discharge_text = generate_discharge_summary(st.session_state.patient_data)
            st.session_state.discharge_summary = discharge_text
            st.success("Discharge summary generated!")

# Display and edit discharge summary
st.header("3. AI-Generated Discharge Summary")

if st.session_state.discharge_summary:
    # Allow editing of the summary
    edited_summary = st.text_area("Review and Edit Summary", st.session_state.discharge_summary, height=500)

    # Update the session state with the edited summary
    st.session_state.discharge_summary = edited_summary

    # Option to download the PDF
    st.header("4. Generate PDF")
    if st.button("Generate PDF"):
        try:
            pdf_data = generate_pdf(st.session_state.patient_data, edited_summary)

            # Provide download button for the PDF
            st.download_button(
                label="Download Discharge Summary PDF",
                data=pdf_data,
                file_name=f"discharge_summary_{st.session_state.patient_data['patient_info']['last_name']}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
else:
    st.info("No discharge summary generated yet. Please generate a summary first.")

# Footer
st.markdown("---")
st.caption("AI-Powered Discharge Summary Generator - For demonstration purposes only")
