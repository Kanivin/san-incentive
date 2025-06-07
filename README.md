 **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # For Linux/Mac
   venv\Scripts\activate      # For Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
python manage.py makemigrations incentives
python manage.py migrate

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   
# Docker Config

docker build -t san-incentive .
docker run -d -p 8000:8000 --name san-incentive-container san-incentive


# Cloud run Set Up
# power shell

gcloud auth login
gcloud builds submit --config preprod-san-incentive.yaml --region=asia-east1

gcloud  run services add-iam-policy-binding --region=asia-southeast1 --member=allUsers --role=roles/run.invoker san-incentive