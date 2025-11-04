# YouTube Transcription API Endpoints

This document provides a detailed overview of the available endpoints for the YouTube Transcription API.

## 1. Root

A simple endpoint to verify that the API is running and accessible.

- **URL:** `/`
- **Method:** `GET`
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "message": "Welcome to the YouTube Transcription API"
    }
    ```

---

## 2. Transcribe YouTube Video

This endpoint downloads the audio from a specified YouTube video URL, processes it through the `faster-whisper` model, and returns the transcription.

- **URL:** `/transcribe`
- **Method:** `POST`
- **Request Body:**
  - **Content-Type:** `application/json`
  - **Payload:**
    ```json
    {
      "youtube_url": "string"
    }
    ```
  - **Example:**
    ```json
    {
      "youtube_url": "https://www.youtube.com/watch?v=your_video_id"
    }
    ```
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "transcription": "The full transcribed text from the video audio.",
      "youtube_url": "https://www.youtube.com/watch?v=your_video_id"
    }
    ```
- **Error Responses:**
  - **Code:** `500 Internal Server Error`
  - **Description:** This error can occur for several reasons:
    - The Whisper model failed to load or is not available.
    - The audio could not be downloaded from the provided YouTube URL.
    - An unexpected error occurred during the transcription process.
  - **Content:**
    ```json
    {
      "detail": "A message describing the error."
    }
    ```
