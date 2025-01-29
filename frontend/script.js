let currentFilePath = null;
let currentMaterialId = null;
let mcqData = null;
let userAnswers = {};
let questionsAnswered = 0;

// Handle file selection
document.getElementById('pdfFile').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('file-name').textContent = `Selected: ${file.name}`;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload_pdf/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.material_id) {
                currentMaterialId = data.material_id;
                currentFilePath = data.file_path;
                document.getElementById('generate-mcq').disabled = false;
                showStatus('File uploaded successfully!', 'success');
            } else {
                showStatus('Error uploading file', 'error');
            }
        } catch (error) {
            showStatus('Error uploading file: ' + error.message, 'error');
        }
    }
});

// Handle MCQ generation
document.getElementById('generate-mcq').addEventListener('click', async () => {
    if (!currentMaterialId) return;

    try {
        // Show progress indicator
        const progressSection = document.getElementById('generation-progress');
        progressSection.style.display = 'block';
        document.getElementById('generate-mcq').disabled = true;

        const response = await fetch(`/generate_mcqs/${currentMaterialId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        mcqData = await response.json();
        if (mcqData.mcqs) {
            displayMCQs(mcqData.mcqs);
            showStatus(`Generated ${mcqData.num_questions} questions`, 'success');
        } else {
            showStatus('Error generating MCQs', 'error');
        }
    } catch (error) {
        showStatus('Error generating MCQs: ' + error.message, 'error');
    } finally {
        // Hide progress indicator
        document.getElementById('generation-progress').style.display = 'none';
    }
});

function displayMCQs(mcqs) {
    const container = document.getElementById('mcq-container');
    container.innerHTML = '';
    
    // Reset answers and count
    userAnswers = {};
    questionsAnswered = 0;

    // Take only the first 5 MCQs
    const displayMcqs = mcqs.slice(0, 5);

    displayMcqs.forEach((mcq, questionIndex) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'mcq-question';
        questionDiv.innerHTML = `
            <h3>Question ${questionIndex + 1} of 5:</h3>
            <p>${mcq.question}</p>
            <ul class="options-list">
                ${mcq.options.map((option, index) => `
                    <li class="option-item" 
                        onclick="selectOption(${questionIndex}, '${option}')"
                        data-option="${option}">
                        ${String.fromCharCode(65 + index)}. ${option}
                    </li>
                `).join('')}
            </ul>
            <div class="explanation" id="explanation-${questionIndex}" style="display: none;">
                ${mcq.explanation}
            </div>
        `;
        container.appendChild(questionDiv);
    });

    // Show Generate Score button
    const scoreButton = document.getElementById('generate-score');
    scoreButton.style.display = 'block';
    scoreButton.disabled = true;
}

function selectOption(questionIndex, selectedOption) {
    if (userAnswers[questionIndex] !== undefined) {
        return; // Prevent changing answer
    }

    const questionDiv = document.querySelectorAll('.mcq-question')[questionIndex];
    const options = questionDiv.querySelectorAll('.option-item');
    
    options.forEach(option => {
        option.classList.remove('selected');
    });

    const selectedElement = Array.from(options).find(
        option => option.dataset.option === selectedOption
    );
    selectedElement.classList.add('selected');

    userAnswers[questionIndex] = selectedOption;
    questionsAnswered++;

    // Enable Generate Score button if all questions are answered
    document.getElementById('generate-score').disabled = questionsAnswered < 5;
}

// Add event listener for Generate Score button
document.getElementById('generate-score').addEventListener('click', () => {
    let score = 0;
    const questions = document.querySelectorAll('.mcq-question');

    // Calculate score and show correct/incorrect answers
    questions.forEach((questionDiv, index) => {
        const options = questionDiv.querySelectorAll('.option-item');
        const userAnswer = userAnswers[index];
        const correctAnswer = mcqData.mcqs[index].correct_answer;
        const explanation = document.getElementById(`explanation-${index}`);

        options.forEach(option => {
            if (option.dataset.option === userAnswer) {
                if (userAnswer === correctAnswer) {
                    option.classList.add('correct');
                    score++;
                } else {
                    option.classList.add('incorrect');
                }
            } else if (option.dataset.option === correctAnswer) {
                option.classList.add('correct');
            }
        });

        // Show explanation
        explanation.style.display = 'block';
    });

    // Display score
    const scoreDisplay = document.getElementById('score-display');
    const percentage = (score / 5) * 100;
    let feedback = '';
    
    if (percentage === 100) {
        feedback = 'Excellent! Perfect score!';
    } else if (percentage >= 80) {
        feedback = 'Great job! Very good performance!';
    } else if (percentage >= 60) {
        feedback = 'Good effort! Keep practicing!';
    } else {
        feedback = 'Keep practicing! You can improve!';
    }

    scoreDisplay.innerHTML = `
        <h2>Quiz Results</h2>
        <p class="final-score">Your Score: ${score}/5 (${percentage}%)</p>
        <p class="feedback">${feedback}</p>
        <button class="button" onclick="location.reload()">Try Another Quiz</button>
    `;
    scoreDisplay.style.display = 'block';
    scoreDisplay.className = `score-section ${getScoreClass(percentage)}`;

    // Disable Generate Score button after showing results
    document.getElementById('generate-score').disabled = true;
});

function getScoreClass(percentage) {
    if (percentage >= 80) return 'excellent';
    if (percentage >= 60) return 'good';
    if (percentage >= 40) return 'average';
    return 'needs-improvement';
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.className = type;
} 