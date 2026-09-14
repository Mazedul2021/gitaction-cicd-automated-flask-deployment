
# CI/CD with GitHub Actions

A simple guide to deploy a Dockerized application to an Azure VM automatically using Blue-Green deployment with GitHub Actions.

---

## 1. Create an Azure VM

Create an Azure Virtual Machine with an SSH key.

The Azure free tier is sufficient for testing.

Make sure you have:

- VM Public IP
- SSH private key (`.pem`)
- VM username (for example: `azureuser`)

---

## 2. Install Docker on the VM

SSH into your VM and run:

```bash
sudo apt update -y
sudo apt install -y docker.io

sudo usermod -aG docker $USER
sudo reboot
```

After reconnecting to the VM, check Docker:

```bash
sudo systemctl status docker
docker ps
```

---

## 3. Configure VM Network Ports

Add the following inbound ports to the VM's Network Security Group:

| Port | Purpose |
|------|---------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 5000 | Application (optional) |

> If Nginx is used as a reverse proxy, port `80` or `443` is normally enough for public access.

---

## 4. Create GitHub Repository Secrets

Go to:

**GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Secret | Value |
|--------|-------|
| `AZURE_HOST` | Your VM public IP |
| `AZURE_KEY` | Content of your SSH private key (`.pem`) |
| `AZURE_USER` | Your VM username, for example `azureuser` |
| `DOCKER_USERNAME` | Your Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub Personal Access Token (PAT) |

---

## 5. Create GitHub Actions Workflow

Create the following directory inside your repository:

```text
.github/workflows/
```

Then create:

```text
.github/workflows/main.yaml
```

Copy the GitHub Actions workflow into `main.yaml`.

Example project structure:

```text
project/
│
├── .github/
│   └── workflows/
│       └── main.yaml
│
├── app.py
├── Dockerfile
├── requirements.txt
└── ...
```

---

## 6. Push Changes to GitHub

Make a change to your application and push it to GitHub:

```bash
git add .
git commit -m "Update application"
git push origin main
```

The GitHub Actions workflow will automatically trigger.

The deployment process:

```text
GitHub
   ↓
GitHub Actions
   ↓
Build Docker Image
   ↓
Push Image to Docker Hub
   ↓
Connect to Azure VM
   ↓
Pull New Image
   ↓
Run New Container
```

---

## 7. Check the Application

After the GitHub Action completes successfully, open:

```text
http://YOUR_VM_PUBLIC_IP
```

If your application is running directly on port `5000`, use:

```text
http://YOUR_VM_PUBLIC_IP:5000
```

You should see your application in the browser.

---

## 8. Verify the Deployment

Check the running containers from the VM:

```bash
docker ps
```

Check the application health:

```bash
curl http://127.0.0.1/health
```

A healthy application should return:

```json
{
  "database": "connected",
  "status": "healthy"
}
```

---

## CI/CD Complete

Now whenever you push changes to the `main` branch:

```bash
git push origin main
```

GitHub Actions will automatically build and deploy the latest version of your application to the Azure VM.