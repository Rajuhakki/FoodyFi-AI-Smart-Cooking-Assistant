/**
 * FoodyFi - Interactive AI Smart Cooking Assistant JS
 */

document.addEventListener('DOMContentLoaded', () => {
    initVoiceInput();
    initVisionUpload();
    initSmartChips();
    initRatingSystem();
    initLoadingOverlay();
});


/* -------------------------------------------------------------
 * 1. VOICE INPUT (Web Speech Recognition API)
 * ------------------------------------------------------------- */
function initVoiceInput() {
    const micBtn = document.getElementById('mic-btn');
    const inputArea = document.getElementById('ingredients-input');

    if (!micBtn || !inputArea) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        micBtn.style.display = 'none';
        console.warn('Web Speech Recognition API is not supported in this browser.');
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    let isListening = false;

    micBtn.addEventListener('click', () => {
        if (!isListening) {
            recognition.start();
            micBtn.classList.add('mic-active');
            micBtn.innerHTML = '<i class="fas fa-microphone-slash"></i> Listening...';
            isListening = true;
        } else {
            recognition.stop();
            resetMicButton();
        }
    });

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (inputArea.value.trim() === '') {
            inputArea.value = transcript;
        } else {
            inputArea.value += ', ' + transcript;
        }
        resetMicButton();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        alert('Voice recognition error: ' + event.error);
        resetMicButton();
    };

    recognition.onend = () => {
        resetMicButton();
    };

    function resetMicButton() {
        isListening = false;
        micBtn.classList.remove('mic-active');
        micBtn.innerHTML = '<i class="fas fa-microphone"></i> Speak Ingredients';
    }
}

/* -------------------------------------------------------------
 * 2. VISION API - IMAGE TO INGREDIENT DETECTION
 * ------------------------------------------------------------- */
function initVisionUpload() {
    const fileInput = document.getElementById('vision-file-input');
    const uploadBtn = document.getElementById('vision-upload-btn');
    const inputArea = document.getElementById('ingredients-input');

    if (!fileInput || !uploadBtn || !inputArea) return;

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        // UI feedback
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting Ingredients...';

        try {
            const csrfToken = getCookie('csrftoken');
            const response = await fetch('/detect-ingredients/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            });

            const data = await response.json();

            if (data.success && data.ingredients) {
                if (inputArea.value.trim() === '') {
                    inputArea.value = data.ingredients;
                } else {
                    inputArea.value += ', ' + data.ingredients;
                }
            } else {
                alert('Could not detect ingredients: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Vision upload error:', error);
            alert('Failed to analyze image.');
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fas fa-camera"></i> Detect from Photo';
            fileInput.value = '';
        }
    });
}

/* -------------------------------------------------------------
 * 3. SMART INGREDIENT SUGGESTION CHIPS
 * ------------------------------------------------------------- */
function initSmartChips() {
    const chips = document.querySelectorAll('.chip');
    const inputArea = document.getElementById('ingredients-input');

    if (!inputArea) return;

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const val = chip.getAttribute('data-value');
            const current = inputArea.value.trim();
            
            if (!current) {
                inputArea.value = val;
            } else if (!current.toLowerCase().includes(val.toLowerCase())) {
                inputArea.value += ', ' + val;
            }
        });
    });
}

/* -------------------------------------------------------------
 * 4. INTERACTIVE STAR RATING SYSTEM
 * ------------------------------------------------------------- */
function initRatingSystem() {
    const ratingContainer = document.getElementById('rating-widget');
    if (!ratingContainer) return;

    const stars = ratingContainer.querySelectorAll('i');
    const recipeId = ratingContainer.getAttribute('data-recipe-id');

    stars.forEach(star => {
        star.addEventListener('click', async () => {
            const ratingValue = star.getAttribute('data-value');

            try {
                const csrfToken = getCookie('csrftoken');
                const formData = new FormData();
                formData.append('value', ratingValue);

                const response = await fetch(`/recipe/${recipeId}/rate/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                });

                const data = await response.json();
                if (data.success) {
                    // Update star displays
                    updateStarUI(stars, ratingValue);
                    const avgDisplay = document.getElementById('avg-rating-display');
                    const countDisplay = document.getElementById('ratings-count-display');
                    if (avgDisplay) avgDisplay.textContent = data.avg_rating;
                    if (countDisplay) countDisplay.textContent = `(${data.ratings_count} ratings)`;
                }
            } catch (err) {
                console.error('Rating error:', err);
            }
        });
    });

    function updateStarUI(starElements, selectedVal) {
        starElements.forEach(s => {
            const val = parseInt(s.getAttribute('data-value'));
            if (val <= selectedVal) {
                s.className = 'fas fa-star';
            } else {
                s.className = 'far fa-star';
            }
        });
    }
}

/* -------------------------------------------------------------
 * 5. LOADING OVERLAY CONTROL
 * ------------------------------------------------------------- */
function initLoadingOverlay() {
    const form = document.getElementById('generate-recipe-form');
    const overlay = document.getElementById('loading-overlay');

    if (form && overlay) {
        form.addEventListener('submit', () => {
            overlay.style.display = 'flex';
        });
    }
}

/* -------------------------------------------------------------
 * 6. STEP-BY-STEP INTERACTIVE COOKING MODE & TEXT-TO-SPEECH
 * ------------------------------------------------------------- */
function initCookingMode() {
    const cookingContainer = document.getElementById('cooking-assistant-app');
    if (!cookingContainer) return;

    let steps = [];
    const stepsScript = document.getElementById('cooking-steps-data');
    
    if (stepsScript && stepsScript.textContent.trim()) {
        try {
            steps = JSON.parse(stepsScript.textContent);
        } catch (e) {
            console.error('Error parsing steps from script tag:', e);
        }
    }

    if (!steps || steps.length === 0) {
        const rawSteps = cookingContainer.getAttribute('data-steps');
        if (rawSteps) {
            try {
                steps = JSON.parse(rawSteps);
            } catch (e) {
                try {
                    const parser = new DOMParser();
                    const decoded = parser.parseFromString(rawSteps, 'text/html').body.textContent;
                    steps = JSON.parse(decoded);
                } catch(err) {
                    console.error('Failed to parse data-steps fallback', err);
                }
            }
        }
    }

    const stepTextEl = document.getElementById('current-step-text');
    if ((!steps || steps.length === 0) && stepTextEl) {
        steps = [stepTextEl.textContent.trim()];
    }

    if (!steps || steps.length === 0) return;

    let currentIndex = 0;
    const totalSteps = steps.length;

    const stepNumEl = document.getElementById('current-step-number');
    const progressBar = document.getElementById('cooking-progress-bar');
    const prevBtn = document.getElementById('prev-step-btn');
    const nextBtn = document.getElementById('next-step-btn');
    const ttsBtn = document.getElementById('tts-btn');
    const ttsTextEl = document.getElementById('tts-btn-text');
    const voiceCmdBtn = document.getElementById('voice-cmd-btn');
    const voiceCmdTextEl = document.getElementById('voice-cmd-btn-text');
    const voiceCmdStatus = document.getElementById('voice-cmd-status');
    const finishScreen = document.getElementById('cooking-finish-screen');
    const stepCard = document.getElementById('main-step-card');

    let isSpeaking = false;

    function renderStep() {
        stopSpeech();
        if (currentIndex < totalSteps) {
            if (stepCard) stepCard.style.display = 'block';
            if (finishScreen) finishScreen.style.display = 'none';

            if (stepTextEl) stepTextEl.textContent = steps[currentIndex];
            if (stepNumEl) stepNumEl.textContent = `STEP ${currentIndex + 1} OF ${totalSteps}`;
            
            if (progressBar) {
                const progress = ((currentIndex + 1) / totalSteps) * 100;
                progressBar.style.width = `${progress}%`;
            }

            if (prevBtn) prevBtn.disabled = (currentIndex === 0);
            if (nextBtn) {
                nextBtn.innerHTML = (currentIndex === totalSteps - 1) ? 
                    'Finish Cooking <i class="fas fa-check"></i>' : 
                    'Next Step <i class="fas fa-arrow-right"></i>';
            }
        } else {
            if (stepCard) stepCard.style.display = 'none';
            if (finishScreen) finishScreen.style.display = 'block';
            if (progressBar) progressBar.style.width = '100%';
        }
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentIndex < totalSteps) {
                currentIndex++;
                renderStep();
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                renderStep();
            }
        });
    }

    // ---------------------------------------------------------
    // Voice Assistant - Text To Speech (Read Step Aloud)
    // ---------------------------------------------------------
    if (ttsBtn && 'speechSynthesis' in window) {
        ttsBtn.addEventListener('click', () => {
            if (isSpeaking) {
                stopSpeech();
            } else {
                speakCurrentStep();
            }
        });
    } else if (ttsBtn) {
        ttsBtn.style.display = 'none';
    }

    function speakCurrentStep() {
        stopSpeech();
        if (!steps[currentIndex]) return;

        const textToSpeak = steps[currentIndex];
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        utterance.onstart = () => {
            isSpeaking = true;
            if (ttsBtn) {
                ttsBtn.style.background = 'rgba(59, 130, 246, 0.25)';
                ttsBtn.style.borderColor = '#3b82f6';
                if (ttsTextEl) ttsTextEl.textContent = 'Speaking Step... (Click to Stop)';
            }
        };

        utterance.onend = () => {
            resetTtsBtn();
        };

        utterance.onerror = (e) => {
            console.error('TTS error:', e);
            resetTtsBtn();
        };

        window.speechSynthesis.speak(utterance);
    }

    function stopSpeech() {
        if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        resetTtsBtn();
    }

    function resetTtsBtn() {
        isSpeaking = false;
        if (ttsBtn) {
            ttsBtn.style.background = '';
            ttsBtn.style.borderColor = '';
            if (ttsTextEl) ttsTextEl.textContent = 'Listen Step (Voice Assistant)';
        }
    }

    // ---------------------------------------------------------
    // Hands-Free Voice Commands (Web Speech Recognition)
    // ---------------------------------------------------------
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let isListeningCmd = false;
    let cmdRecognition = null;

    if (voiceCmdBtn && SpeechRecognition) {
        cmdRecognition = new SpeechRecognition();
        cmdRecognition.continuous = true;
        cmdRecognition.interimResults = false;
        cmdRecognition.lang = 'en-US';

        voiceCmdBtn.addEventListener('click', () => {
            if (!isListeningCmd) {
                try {
                    cmdRecognition.start();
                    isListeningCmd = true;
                    voiceCmdBtn.style.background = 'rgba(239, 68, 68, 0.2)';
                    voiceCmdBtn.style.borderColor = '#ef4444';
                    if (voiceCmdTextEl) voiceCmdTextEl.textContent = 'Listening Commands...';
                    if (voiceCmdStatus) voiceCmdStatus.style.display = 'block';
                } catch(e) {
                    console.error('Speech recognition start error:', e);
                }
            } else {
                stopVoiceCmd();
            }
        });

        cmdRecognition.onresult = (event) => {
            const lastIndex = event.results.length - 1;
            const transcript = event.results[lastIndex][0].transcript.toLowerCase().trim();
            console.log('Voice Command Received:', transcript);

            if (transcript.includes('next') || transcript.includes('forward')) {
                if (currentIndex < totalSteps) {
                    currentIndex++;
                    renderStep();
                }
            } else if (transcript.includes('back') || transcript.includes('previous')) {
                if (currentIndex > 0) {
                    currentIndex--;
                    renderStep();
                }
            } else if (transcript.includes('listen') || transcript.includes('read') || transcript.includes('speak') || transcript.includes('repeat')) {
                speakCurrentStep();
            } else if (transcript.includes('stop') || transcript.includes('pause')) {
                stopSpeech();
            }
        };

        cmdRecognition.onerror = (event) => {
            console.warn('Voice command recognition error:', event.error);
        };

        cmdRecognition.onend = () => {
            if (isListeningCmd) {
                // Restart automatically if still listening mode
                try { cmdRecognition.start(); } catch(e) {}
            } else {
                stopVoiceCmd();
            }
        };

        function stopVoiceCmd() {
            isListeningCmd = false;
            if (cmdRecognition) {
                try { cmdRecognition.stop(); } catch(e) {}
            }
            if (voiceCmdBtn) {
                voiceCmdBtn.style.background = '';
                voiceCmdBtn.style.borderColor = '';
                if (voiceCmdTextEl) voiceCmdTextEl.textContent = 'Hands-Free Commands';
            }
            if (voiceCmdStatus) voiceCmdStatus.style.display = 'none';
        }
    } else if (voiceCmdBtn) {
        voiceCmdBtn.style.display = 'none';
    }

    renderStep();
}


/* Helper to retrieve CSRF token */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
