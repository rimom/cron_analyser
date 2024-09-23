
# Cron Job Visualizer

Cron Job Visualizer is a web application that helps you visualize your cron jobs' schedules. By inputting raw cron job data, the app converts it into structured JSON and generates a Gantt chart, allowing you to easily see when and how often your cron jobs are scheduled to run.

## Features

- **Cron Parsing**: Automatically parses raw cron job data into structured JSON format.
- **Interactive Gantt Chart**: Visualizes cron job schedules with an interactive, zoomable Gantt chart using Plotly.
- **Schedule Overlap Detection**: Helps you identify potential overlaps between cron jobs.

## How It Works

1. **Input**: Paste cron job schedules in plain text (e.g., from `crontab -l` or `.magento.app.yaml`).
2. **Processing**: The cron schedules are parsed and converted into a JSON format.
3. **Visualization**: The app generates an interactive Gantt chart that shows the cron job schedule and their execution times over a user-specified time period.

## Technologies Used

- **Flask**: For handling HTTP requests and serving the web interface.
- **OpenAI API**: Used to parse and structure cron job data.
- **Plotly**: For rendering the interactive Gantt chart.
- **croniter**: For calculating the next execution times based on cron schedules.
- **dotenv**: For loading environment variables like API keys.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/cron-job-visualizer.git
   cd cron-job-visualizer
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your OpenAI API key:

   ```bash
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Run the application:

   ```bash
   python app.py
   ```

5. Open a browser and navigate to `http://localhost:5000` to use the application.

## Usage

1. Paste your cron schedules into the input box.
2. Choose a timeframe (in hours) for the Gantt chart.
3. Click "Generate Chart" to visualize the cron job schedules.
4. Optionally, view the parsed JSON for the cron jobs by clicking the "Display the Parsed JSON" button.

## Example

Here’s an example of inputting cron schedules and generating the Gantt chart:

```
*/5 * * * * job_1
*/10 * * * * job_2
0 0 * * * job_3
```

After clicking "Generate Chart," you will see a timeline displaying when each job is scheduled to run.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue to report any bugs or suggest improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/license/mit) for details.

---

**Disclaimer**: This tool is for visualization purposes only. It does not execute cron jobs or handle their logic. It is designed to help identify overlaps and visualize scheduling.

---

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [Plotly](https://plotly.com/)
- [OpenAI](https://openai.com/)
- [croniter](https://github.com/taichino/croniter)
