from flask import Flask, render_template, request, redirect, url_for
import os
import pickle
import docx
import docx2txt
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Load pre-trained models for categorization
svc_model = pickle.load(open('models/clf.pkl', 'rb'))
tfidf = pickle.load(open('models/tfidf.pkl', 'rb'))
le = pickle.load(open('models/encoder.pkl', 'rb'))

# Helper function to clean resume text
def cleanResume(txt):
    txt = re.sub('http\S+\s', ' ', txt)
    txt = re.sub('RT|cc', ' ', txt)
    txt = re.sub('#\S+', '', txt)
    txt = re.sub('@\S+', ' ', txt)
    txt = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', txt)
    txt = re.sub(r'[^\x00-\x7f]', ' ', txt)
    txt = re.sub('\s+', ' ', txt)
    return txt

# Helper function to extract text from different file types
def extract_text(uploaded_file):
    file_extension = uploaded_file.filename.split('.')[-1].lower()
    text = ''
    if file_extension == 'pdf':
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text()
    elif file_extension == 'docx':
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + '\n'
    elif file_extension == 'txt':
        text = uploaded_file.read().decode('utf-8', errors='ignore')
    return text

# Function for resume categorization
def predict_category(resume_text):
    cleaned_text = cleanResume(resume_text)
    vectorized_text = tfidf.transform([cleaned_text])
    vectorized_text_dense = vectorized_text.toarray()
    predicted_label = svc_model.predict(vectorized_text_dense)
    return le.inverse_transform(predicted_label)[0]


# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Resume Categorization Route
@app.route('/categorization', methods=['GET', 'POST'])
def categorization():
    if request.method == 'POST':
        uploaded_file = request.files['resume']
        if uploaded_file:
            resume_text = extract_text(uploaded_file)
            category = predict_category(resume_text)
            return render_template('results.html', mode='categorization', category=category)
    return render_template('categorization.html')


# Resume and Job Matching Route
@app.route('/matching', methods=['GET', 'POST'])
def matching():
    if request.method == 'POST':
        job_description = request.form['job_description']
        resume_files = request.files.getlist('resumes')
        resumes = []

        for resume_file in resume_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(file_path)
            resumes.append(extract_text(resume_file))

        if not resumes or not job_description:
            return render_template('matching.html', message="Please upload resumes and enter a job description.")

        # Vectorize job description and resumes
        vectorizer = TfidfVectorizer().fit_transform([job_description] + resumes)
        vectors = vectorizer.toarray()

        # Calculate cosine similarities
        job_vector = vectors[0]
        resume_vectors = vectors[1:]
        similarities = cosine_similarity([job_vector], resume_vectors)[0]

        # Get top 3 resumes and their similarity scores
        top_indices = similarities.argsort()[-5:][::-1]
        top_resumes = [resume_files[i].filename for i in top_indices]
        similarity_scores = [round(similarities[i], 2) for i in top_indices]

        return render_template('results.html', mode='matching', matches=zip(top_resumes, similarity_scores))

    return render_template('matching.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
