"""
Browser audio capture diagnostic tool.
This script navigates to a public video site and attempts to record with audio
to diagnose browser audio capture capabilities.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_manager import BrowserManager

import logger
log = logger

def diagnose_audio_capture():
    """Diagnose if browser can capture audio from a video element on a public site."""
    # Initialize browser
    browser_manager = BrowserManager(headless=False, browser_type="chrome")
    driver = browser_manager.initialize()
    
    try:
        # Navigate to a public site with videos
        log.info("Navigating to a public video site")
        driver.get("https://www.w3schools.com/html/html5_video.asp")
        
        # Wait for video element to load
        wait = WebDriverWait(driver, 10)
        video = wait.until(EC.presence_of_element_located((By.ID, "video1")))
        
        log.info("Starting video playback")
        # Play the video with audio
        driver.execute_script("arguments[0].play(); arguments[0].muted = false;", video)
        
        # Wait for video to start playing
        time.sleep(3)
        
        # Create output directory
        output_dir = "audio_diagnostic_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use JavaScript to record the video with audio
        log.info("Starting recording with audio")
        recording_script = """
        return (async () => {
            try {
                // Get the video element
                const videoElement = document.getElementById('video1');
                if (!videoElement) {
                    console.error('Video element not found');
                    return { success: false, error: 'Video element not found' };
                }
                
                // Ensure video is unmuted
                videoElement.muted = false;
                videoElement.volume = 1.0;
                
                // Create canvas for capturing
                const canvas = document.createElement('canvas');
                canvas.width = videoElement.videoWidth;
                canvas.height = videoElement.videoHeight;
                const ctx = canvas.getContext('2d');
                
                // Initialize recording variables
                let canvasStream = canvas.captureStream();
                let combinedStream = canvasStream;
                
                // Method 1: Try to get audio from the video element directly
                console.log('Attempting to capture audio from video element');
                if (videoElement.captureStream) {
                    console.log('Using video element captureStream for audio');
                    const videoStream = videoElement.captureStream();
                    const audioTracks = videoStream.getAudioTracks();
                    
                    if (audioTracks.length > 0) {
                        console.log('Found audio track in video element:', audioTracks[0].label);
                        // Add the audio track to our canvas stream
                        canvasStream.addTrack(audioTracks[0]);
                        console.log('Added audio track to canvas stream');
                    } else {
                        console.log('No audio tracks found in video element stream');
                    }
                }
                
                // Method 2: Try to get system audio permission
                try {
                    console.log('Requesting user audio...');
                    const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    console.log('Received audio stream');
                    
                    // Create a new MediaStream with both video and audio
                    const newStream = new MediaStream();
                    
                    // Add all video tracks from canvas stream
                    canvasStream.getVideoTracks().forEach(track => {
                        newStream.addTrack(track);
                    });
                    
                    // Add all audio tracks from audio stream
                    audioStream.getAudioTracks().forEach(track => {
                        console.log('Adding audio track:', track.label);
                        newStream.addTrack(track);
                    });
                    
                    // Use the combined stream
                    combinedStream = newStream;
                    console.log('Created combined stream with video and system audio');
                } catch (e) {
                    console.log('Could not get system audio:', e);
                }
                
                // Find a supported codec with audio
                const codecsToTry = [
                    'video/webm; codecs=vp9,opus',
                    'video/webm; codecs=vp8,opus',
                    'video/webm; codecs=vp9',
                    'video/webm; codecs=vp8',
                    'video/webm'
                ];
                
                let mimeType = '';
                for (const codec of codecsToTry) {
                    if (MediaRecorder.isTypeSupported(codec)) {
                        mimeType = codec;
                        console.log('Using codec:', codec);
                        break;
                    }
                }
                
                if (!mimeType) {
                    return { success: false, error: 'No supported codec found' };
                }
                
                // Create the media recorder with audio settings
                const recorderOptions = {
                    mimeType: mimeType,
                    videoBitsPerSecond: 2500000,  // 2.5 Mbps
                    audioBitsPerSecond: 128000    // 128 kbps audio
                };
                
                let recorder = new MediaRecorder(combinedStream, recorderOptions);
                let chunks = [];
                
                recorder.ondataavailable = e => {
                    if (e.data.size > 0) {
                        chunks.push(e.data);
                    }
                };
                
                // Start recording
                console.log('Starting recording for 5 seconds');
                recorder.start();
                
                // Draw video frames to canvas
                const drawFrame = () => {
                    if (videoElement.paused || videoElement.ended) return;
                    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                    requestAnimationFrame(drawFrame);
                };
                drawFrame();
                
                // Record for 5 seconds
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                // Stop recording
                recorder.stop();
                
                // Wait for data to be available
                return new Promise(resolve => {
                    recorder.onstop = () => {
                        const blob = new Blob(chunks, { type: 'video/webm' });
                        console.log('Recording finished, blob size:', blob.size);
                        
                        // Convert blob to base64
                        const reader = new FileReader();
                        reader.readAsDataURL(blob);
                        reader.onloadend = () => {
                            const base64data = reader.result;
                            resolve({ 
                                success: true, 
                                base64: base64data,
                                audioTracks: combinedStream.getAudioTracks().length,
                                blob_size: blob.size
                            });
                        };
                    };
                });
            } catch (error) {
                console.error('Recording error:', error);
                return { success: false, error: error.toString() };
            }
        })();
        """
        
        result = driver.execute_script(recording_script)
        
        if result and result.get('success'):
            log.info(f"Recording successful! Blob size: {result.get('blob_size')}")
            log.info(f"Audio tracks detected: {result.get('audioTracks')}")
            
            # Save base64 data to a file
            base64_data = result.get('base64')
            if base64_data:
                # Remove the data URL prefix
                base64_data = base64_data.split(',')[1]
                
                # Save to file
                import base64
                output_path = os.path.join(output_dir, "recording.webm")
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(base64_data))
                log.info(f"Saved recording to {output_path}")
                
                # Convert to MP4 with audio
                try:
                    import subprocess
                    mp4_path = os.path.join(output_dir, "recording.mp4")
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', output_path,
                        '-c:v', 'libx264',
                        '-crf', '22',
                        '-preset', 'medium',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-ac', '2',
                        '-ar', '48000',
                        '-strict', 'experimental',
                        mp4_path
                    ]
                    log.info(f"Converting to MP4 with command: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True)
                    log.info(f"Converted to MP4: {mp4_path}")
                except Exception as e:
                    log.error(f"Error converting to MP4: {e}")
        else:
            log.error(f"Recording failed: {result.get('error')}")
        
    except Exception as e:
        log.error(f"Error during audio test: {e}")
    finally:
        # Close browser
        if driver:
            driver.quit()

if __name__ == "__main__":
    diagnose_audio_capture()