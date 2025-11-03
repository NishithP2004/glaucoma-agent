# 👁️ Glaucoma Agent – Frontend

A Streamlit UI to upload retinal fundus images and view the Glaucoma Agent’s diagnosis with an annotated image.

## Run locally

1) Install dependencies

```bash
pip install -r requirements.txt
```

2) Start the app

```bash
streamlit run streamlit_app.py
```

3) Configure backend

- In the app sidebar, set the "Colab Server URL" to your Flask/ngrok URL that exposes `POST /predict`.
- By default, it uses:

```
https://dominant-usually-oyster.ngrok-free.app
```

## Expected backend contract

Endpoint: `POST {SERVER_URL}/predict`

- form-data key `image`: the uploaded fundus image file
- JSON response (example):

```json
{
  "classification": "glaucoma suspect",
  "detail": "Increased cup-to-disc ratio with suspicious rim thinning.",
  "ratio": 0.63,
  "annotated_image_url": "https://<your-ngrok>/artifacts/annotated_123.png"
}
```

The UI displays the classification badge, CDR metric, explanatory detail, and the annotated image when available.
