from flask import Flask, render_template, request
from datetime import datetime, timedelta
from together import Together
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize Together.ai client
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

#changes here
from flask import send_from_directory

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('static', 'ads.txt', mimetype='text/plain')

#changes end
@app.route('/terms')
def terms():
    return render_template('terms.html')

def format_schedule_response(response_text):
    """Format the AI response into clean HTML structure"""
    if "Day 1" in response_text:
        days = response_text.split("\n\n")
        formatted_days = []

        for day in days:
            if not day.strip():
                continue
            parts = day.split("\n", 1)
            if len(parts) == 2:
                day_title, day_content = parts
                formatted_content = day_content.replace("\n- ", "<br>- ").replace("\n", "<br>")
                formatted_day = f"""
                <div class="schedule-day">
                    <h3>{day_title}</h3>
                    <div class="day-content">{formatted_content}</div>
                </div>
                """
                formatted_days.append(formatted_day)
        return "\n".join(formatted_days)
    else:
        return response_text.replace("\n", "<br>")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    task = request.form['task']
    days = request.form['days']
    prompt = request.form.get('prompt', '')

    try:
        days_int = int(days)
        deadline_date = datetime.now() + timedelta(days=days_int)
    except ValueError:
        days_int = 0
        deadline_date = None

    full_prompt = f"""
Create a detailed {days}-day schedule for the following task:

Task: {task}
Deadline: {days} days ({deadline_date.strftime('%B %d, %Y') if deadline_date else 'No deadline'})
Additional Details: {prompt if prompt else 'None provided'}

Please structure your response with:
1. Clear day-by-day breakdown (Day 1, Day 2, etc.)
2. Daily milestones and objectives
3. Specific tasks with time allocations
4. Priority tasks marked clearly
5. Practical advice and tips

Format each day as follows:
Day [X]: [Milestone]
- Task 1: [description] (Time: [duration])
- Priority Task: [description]
- Additional notes: [tips/advice]

Make the schedule realistic and achievable. Include rest days if appropriate.
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-Vision-Free",  # change model if you like
            messages=[{
                "role": "user",
                "content": full_prompt
            }]
        )
        raw_result = response.choices[0].message.content
        formatted_result = format_schedule_response(raw_result)
    except Exception as e:
        formatted_result = f"<div class='error'>Error generating schedule: {str(e)}</div>"

    return render_template('index.html',
                           result=formatted_result,
                           task=task,
                           days=days,
                           prompt=prompt,
                           deadline_date=deadline_date.strftime('%B %d, %Y') if deadline_date else None)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/coffee')
def coffee():
    return render_template('coffee.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
