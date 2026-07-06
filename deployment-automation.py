import os
import yaml
import traceback
import subprocess
from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException


# manifest_path = 
def initialize_k8s():
    try:
        kubeconfig_path = os.getenv("KUBECONFIG")

        if kubeconfig_path and os.path.exists(kubeconfig_path):
            print(f"✅ Using kubeconfig: {kubeconfig_path}")
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            print("⚠️ kubeconfig not found in environment variable")
            raise FileNotFoundError("KUBECONFIG is not set or file does not exist")

    except Exception:
        try:
            kubeconfig_path = "/Users/I572887/Desktop/workspace/learning/python/practice/handling-log/deployment-automation/kubeconfigs/demo-kubeconfig.yaml"
            if kubeconfig_path and os.path.exists(kubeconfig_path):
                print(f" Using kubeconfig path: {kubeconfig_path}")
                config.load_kube_config(config_file=kubeconfig_path)
                print("✅ Connected using in-cluster config")
            else:
                print("⚠️ kubeconfig not found, trying default location...")
                config.load_kube_config()
                print("✅ Connected using default kubeconfig")                    
        except Exception as e:
            raise Exception("❌ Unable to connect to Kubernetes cluster") from e

def install_cert_manager():
    url = "https://github.com/cert-manager/cert-manager/releases/download/v1.20.2/cert-manager.yaml"
    manifest_path = "/Users/I572887/Desktop/workspace/learning/python/practice/handling-log/deployment-automation/ammara/cert-manager"
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "cert-manager", "-o", "jsonpath={.items[*].metadata.name}"],
            capture_output=True,
            text=True
        )
        installed_pods = result.stdout.strip()
        print(installed_pods)

        if result.returncode == 0 and installed_pods:
            print("Cert-manager is already installed, skipping installation.")
        else:
            print("cert-manager not installed! Installing cert-manager...")
            subprocess.run(
                ["kubectl", "apply", "-f", os.path.join(manifest_path, "namespace.yaml")],
                check=True,
                capture_output=True,
                text=True
            )
            result = subprocess.run(
                ["kubectl", "apply", "-f", url],
                check=True,
                capture_output=True,
                text=True
            )
            print("Cert-manager installed successfully!")
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        print("Failed to install cert-manager")
        print(e.stderr)
    except Exception as e:
        print(f"Error installing cert-manager: {str(e)}")
        traceback.print_exc()

def run(cmd):
    return subprocess.run(cmd, check=True)

def apply_manifest():
    app_manifest_path = "/Users/I572887/Desktop/workspace/learning/python/practice/handling-log/deployment-automation/ammara/k8s"

    # apply issuer 
    subprocess.run(
        ["kubectl", "apply", "-f", os.path.join(app_manifest_path, "clusterissuer.yaml")],
        check=True,
        capture_output=True,
        text=True
    )
    # verify issuer status
    run([
        "kubectl", "wait", "--for=condition=Ready", "clusterissuer/letsencrypt-prod", "--timeout=120s"
    ])

    # apply secret
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "sample-secret.yaml")
    ])

    # apply pvc
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-mysql-pvc.yaml")
    ])

    # apply mysql
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-mysql-deployment.yaml")
    ])
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-mysql-service.yaml")
    ])

    # install ingress controller

    run(["helm", "repo", "add", "ingress-nginx", "https://kubernetes.github.io/ingress-nginx"])
    run(["helm", "repo", "update"])

    # run("""
    # helm install nginx-ingress ingress-nginx/ingress-nginx \
    # --namespace ingress-nginx \
    # --create-namespace \
    # --set controller.service.type=LoadBalancer
    # """)

    # run("kubectl wait --namespace ingress-nginx \
    # --for=condition=ready pod \
    # --selector=app.kubernetes.io/component=controller \
    # --timeout=180s")

    # apply ingress
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-app-ingress.yaml")
    ])
    # apply app manifest
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-app-deployment.yaml")
    ])
    run([
        "kubectl", "apply", "-f", os.path.join(app_manifest_path, "ammara-app-service.yaml")
    ])      





    

initialize_k8s()
install_cert_manager()
apply_manifest()