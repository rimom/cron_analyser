import os
import openai
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from croniter import croniter
import io
import plotly.express as px
import plotly.graph_objects as go

# Set the Matplotlib backend to 'Agg' to avoid GUI-related issues on MacOS
plt.switch_backend('Agg')

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# OpenAI API Key from .env
openai.api_key = os.getenv('OPENAI_API_KEY')

# Function to communicate with OpenAI API and get the JSON output
def get_parsed_cron_jobs(raw_input):

    #mock response
    return """[
  {
    "job_name": "sm_product_update_default_special_price",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_product_convert_url",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_remind_limit_sent_email",
    "schedule": "0 * * * *"
  },
  {
    "job_name": "sm_sales_email_convert_sending",
    "schedule": "*/15 * * * *"
  },
  {
    "job_name": "sm_sap_auto_tracking",
    "schedule": "0 */4 * * *"
  },
  {
    "job_name": "cleanup",
    "schedule": "0 14,21 * * *"
  },
  {
    "job_name": "send_email_order_ready_to_collect_first",
    "schedule": "*/27 * * * *"
  },
  {
    "job_name": "send_email_order_ready_to_collect_second",
    "schedule": "*/29 * * * *"
  },
  {
    "job_name": "send_email_invoice_paid",
    "schedule": "*/31 * * * *"
  },
  {
    "job_name": "send_reminder",
    "schedule": "* * * * *"
  },
  {
    "job_name": "sm_force_sapexpress_cron",
    "schedule": "00 1,3,5,7,9,11,13,15,17,19,21,23 * * *"
  },
  {
    "job_name": "wavecell_send_order_confirmation",
    "schedule": "*/20 * * * *"
  },
  {
    "job_name": "wavecell_send_payment_verified",
    "schedule": "*/5 * * * *"
  },
  {
    "job_name": "wavecell_send_shipment",
    "schedule": "*/25 * * * *"
  },
  {
    "job_name": "update_status_pre_shipment",
    "schedule": "00 */3 * * *"
  },
  {
    "job_name": "create_purchase_for_order",
    "schedule": "*/10 * * * *"
  },
  {
    "job_name": "create_refund_for_order",
    "schedule": "*/10 * * * *"
  },
  {
    "job_name": "thor_create_refund_for_order",
    "schedule": "0 */4 * * *"
  },
  {
    "job_name": "report_request_failed",
    "schedule": "0 23 * * *"
  },
  {
    "job_name": "sm_product_update_configurable_image",
    "schedule": "*/10 * * * *"
  },
  {
    "job_name": "sm_product_configurable_without_image",
    "schedule": "*/15 * * * *"
  },
  {
    "job_name": "sm_media_product_image_listing",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_media_cms_image_listing",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_media_image_clean",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_remove_invalid_lock_cron",
    "schedule": "*/5 * * * *"
  },
  {
    "job_name": "update_expiry_time",
    "schedule": "*/10 * * * *"
  },
  {
    "job_name": "sm_update_expiry_time_gopay",
    "schedule": "*/10 * * * *"
  },
  {
    "job_name": "sm_product_update_default_special_price",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_product_convert_url",
    "schedule": "*/30 * * * *"
  },
  {
    "job_name": "sm_remind_limit_sent_email",
    "schedule": "0 * * * *"
  },
  {
    "job_name": "sm_sales_email_convert_sending",
    "schedule": "*/15 * * * *"
  },
  {
    "job_name": "sm_sap_auto_tracking",
    "schedule": "0 */4 * * *"
  },
  {
    "job_name": "cleanup",
    "schedule": "0 14,21 * * *"
  }
]"""

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

    # Disabled temporarily due to OpenAI API restrictions, don't remove this code
    response = openai.ChatCompletion.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4'),
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
        
        cron_iter = croniter(schedule, start_time)
        # Simulate for the defined number of hours
        end_time = start_time + timedelta(hours=hours)
        
        while True:
            current_time = cron_iter.get_next(datetime)
            if current_time >= end_time:
                break
            jobs.append(job_name)
            start_times.append(current_time)
            end_times.append(current_time + timedelta(minutes=0.5))
            schedules.append(schedule)
    
    # Create a DataFrame for plotting
    df = pd.DataFrame({
        'Task': jobs,
        'Start': start_times,
        'End': end_times,
        'Schedule': schedules
    })

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
        # autosize=True,
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
    app.run(debug=True)
