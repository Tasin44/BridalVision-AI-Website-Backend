# BridalVision AI Website Backend

![BridalVision AI](https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge&logo=google-gemini)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/DRF-a30000?style=for-the-badge&logo=django&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/celery-%2337814A.svg?style=for-the-badge&logo=celery&logoColor=white)

BridalVision AI is a cutting-edge virtual try-on application that leverages advanced generative AI to seamlessly map bridal dresses onto user-uploaded images. This repository contains the robust, scalable backend powering the platform.

## 🚀 Key Features

- **Advanced AI Virtual Try-On:** Powered by the **Gemini Image Generation API** (`gemini-3.1-flash-image-preview`), allowing users to visualize themselves in different bridal outfits with high fidelity.
- **Intelligent Background Removal:** Uses `rembg` to intelligently remove and replace backgrounds, perfectly compositing the try-on subject into an elegant storefront template with custom branding.
- **Scalable REST API:** Built using **Django** and **Django REST Framework (DRF)**, providing secure, session-based endpoints for users and JWT-authenticated endpoints for administrators.
- **Asynchronous Task Processing:** Uses **Celery** backed by **Redis** to handle heavy AI inference tasks and image processing in the background without blocking API responses.
- **Real-time Capabilities:** Configured with **Django Channels**, **Daphne**, and **Channels-Redis** to support WebSockets for real-time AI generation progress updates.
- **Comprehensive API Documentation:** Automatically generated Swagger/OpenAPI documentation via `drf-yasg`.
- **Payment Integration:** Ready for monetization using **Stripe** integration.
- **Reporting & Data:** Capable of generating PDF reports with `reportlab` and handling data exports via `pandas` and `openpyxl`.

## 🛠️ Technology Stack

### Core Framework & API
- **Python 3**
- **Django** - High-level Python web framework.
- **Django REST Framework (DRF)** - Powerful toolkit for building Web APIs.
- **JWT (SimpleJWT)** - Secure token-based authentication for administrative apps.
- **drf-yasg** - OpenAPI 2.0 (Swagger) schema generation.

### AI & Image Processing
- **Google GenAI SDK** - Integration with Google's Gemini Models for generative try-on.
- **Nano Banana Optimization Pipeline** - Custom image optimization utility (`optimize_for_nano_banana`) to rigorously format, resize, and validate images before AI inference.
- **Rembg** - ML-based tool to remove image backgrounds.
- **Pillow (PIL)** - Extensive image manipulation, compositing, resizing, and filtering.

### Asynchronous & Real-time
- **Celery** - Distributed task queue.
- **Redis** - In-memory data structure store, used as a database, cache, and message broker.
- **Django Channels / Daphne** - WebSockets integration for real-time async communication.

### Database & Storage
- **PostgreSQL** (`psycopg2-binary`) - Robust relational database management.
- **Django Environ / Python Decouple** - Secure environment variable management.

### Deployment & Infrastructure
- **Gunicorn** - Python WSGI HTTP Server.
- **WhiteNoise** - Simplified static file serving for Python web apps.

## 📂 Project Structure

- `aamyproject/` - Main Django settings and core configuration.
- `mainapp/` - User-facing REST APIs, session tracking, and user image models.
- `adminapp/` - Administrator tools to manage dress categories, images, and brand data.
- `geminiaiapp/` - The core AI engine handling communication with the Gemini API, prompt engineering, and image post-processing.

## 💡 How It Works

1. **User Interaction:** A user uploads a photo of themselves and selects a dress category. A temporary session is created to track their progress securely without requiring a hard login.
2. **AI Processing:** The images are optimized and sent to the `gemini-3.1-flash-image-preview` model along with a specialized try-on prompt.
3. **Compositing:** Once the generated try-on image is returned, the backend automatically refines the image, matches store lighting, places the subject on a custom background template, and adds the BridalVision watermark/logo.
4. **Delivery:** The final, high-quality image is stored and served to the user via the API.

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd BridalVision-AI-Website-Backend
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file and populate it with necessary keys (e.g., `GOOGLE_API_KEY`, Database credentials, Stripe keys, Redis URL).

4. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Start Redis & Celery (in separate terminals):**
   ```bash
   redis-server
   celery -A aamyproject worker -l info
   ```

6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
