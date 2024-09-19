import os
import openai
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from croniter import croniter, CroniterNotAlphaError, CroniterBadCronError, CroniterBadDateError
import plotly.express as px

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# OpenAI API Key from .env
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to communicate with OpenAI API and get the JSON output
def get_parsed_cron_jobs(raw_input):
   
    prompt = (
        f"Extract the following cron jobs and convert them into JSON format. Each entry should contain 'job_name' and 'schedule'. "
        f"The input is large, and I need you to process all of it. Do not truncate any part of the input. If a job is missing a schedule, skip it. "
        f"Here is an example of the expected format:\n\n"
        f"[\n"
        f"  {{\n"
        f"    \"job_name\": \"cron_job_1\",\n"
        f"    \"schedule\": \"0 * * * *\"\n"
        f"  }},\n"
        f"  {{\n"
        f"    \"job_name\": \"cron_job_2\",\n"
        f"    \"schedule\": \"*/10 * * * *\"\n"
        f"  }}\n"
        f"]\n\n"
        f"Now, convert the cron jobs listed below to JSON format. Respond only with the plain JSON without any formating, nothing else:\n\n---\n{raw_input}\n---"
    )

    response = openai.ChatCompletion.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats cron jobs into structured JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=15000,
        temperature=0,
    )

    # Get the content of the response
    raw_response = response['choices'][0]['message']['content'].strip()

    # Sanitize the response: remove any possible code block markers (e.g., "```")
    clean_response = raw_response.replace("```", "").strip()

    # Print the sanitized response to debug
    print(clean_response)

    return clean_response

# Helper function to generate the Gantt chart
def generate_gantt_chart(cron_jobs, hours=12):
    # Start time for the simulation (beginning of the day)
    start_time = datetime(2024, 8, 21, 0, 0)
    
    jobs, start_times, end_times, schedules = [], [], [], []

    # Generate start times based on cron expressions
    for job in cron_jobs:
        job_name = job['job_name']
        schedule = job['schedule']
        
        try:
            cron_iter = croniter(schedule, start_time)
            # Simulate for the defined number of hours
            end_time = start_time + timedelta(hours=hours)
            
            while True:
                try:
                    current_time = cron_iter.get_next(datetime)
                    if current_time >= end_time:
                        break
                    jobs.append(job_name)
                    start_times.append(current_time)
                    end_times.append(current_time + timedelta(minutes=0.5))
                    schedules.append(schedule)
                except CroniterBadDateError:
                    print(f"Warning: Could not find next execution time for job '{job_name}' with schedule '{schedule}'")
                    break
        except (CroniterNotAlphaError, CroniterBadCronError) as e:
            print(f"Error: Invalid cron expression for job '{job_name}': {schedule}")
            continue
    
    # Create a DataFrame for plotting
    df = pd.DataFrame({
        'Task': jobs,
        'Start': start_times,
        'End': end_times,
        'Schedule': schedules
    })

    # Check if DataFrame is empty
    if df.empty:
        return "<p>No valid cron jobs to display.</p>"

    # Assign unique colors to each task
    unique_jobs = df['Task'].unique()

    color_map = px.colors.qualitative.Plotly[:len(unique_jobs)]  # Get unique colors from Plotly palette

    # Generate the Gantt chart with Plotly
    fig = px.timeline(df, x_start="Start", x_end="End", y="Task", title="Cron Jobs Schedule",
                      color='Task', color_discrete_sequence=color_map, hover_data=['Schedule'])

    # Set initial zoom window (1 hour)
    initial_range = [start_time, start_time + timedelta(hours=1)]
    
    # Customize the layout for zoom and pan with rangeslider
    fig.update_layout(
        dragmode='pan',
        height=max(10 * len(unique_jobs), 1000),  # Adjust the height based on the number of tasks
        xaxis=dict(
            rangeslider=dict(visible=True),
            range=initial_range,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikethickness=1,
            spikecolor="black",
            tickformat='%H:%M:%S',
            showgrid=True,
        ),
        hovermode='closest',  # Enable hover to see details
        showlegend=True,  # Keep the legend on the right
        yaxis=dict(showticklabels=False, fixedrange=False),
    )

    # Return the Plotly chart
    return fig.to_html(full_html=False, config={
        'scrollZoom': True,
        'displayModeBar': True,
        'displaylogo': False,
        'doubleClick': 'reset',
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    raw_input = request.form.get('cron_input')
    timeframe = request.form.get('timeframe', default=2, type=int)
    
    try:
        parsed_json = get_parsed_cron_jobs(raw_input)
        cron_jobs = json.loads(parsed_json)
    except (json.JSONDecodeError, IndexError) as e:
        print("Error parsing JSON:", e)
        return jsonify({'error': 'Invalid JSON format'})
    
    chart_html = generate_gantt_chart(cron_jobs, hours=timeframe)
    
    return jsonify({
        'chart_html': chart_html,
        'parsed_json': cron_jobs  # Return the parsed JSON as well
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)