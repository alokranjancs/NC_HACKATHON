
## Steps to Replicate 

1. Download the code from git.

2. Get OpenAI API key from this [URL](https://platform.openai.com/account/api-keys). You need to create an account in OpenAI webiste if you haven't already.
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Run the following command in the terminal to install necessary python packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the following command in your terminal to start the NCAssist UI:
   ```
	chainlit run D:\hackathon\NC_HACKATHON\AI_Chabot\solution\NCAssist\appcsv.py -w --port 8083
	chainlit run D:\hackathon\NC_HACKATHON\AI_Chabot\solution\NCAssist\app.py -w --port 8084

   ```
---