# Terraform on AWS – Overview & Commands

This guide provides a concise overview of Terraform, key commands, AWS examples for both new and existing projects, definitions, best practices, and diagrams to help non-experts understand.

---

## 1. Introduction to Terraform

**Terraform** is an open-source Infrastructure as Code (IaC) tool by HashiCorp that enables provisioning, configuring, and managing cloud infrastructure declaratively. You define resources in `.tf` files, and Terraform orchestrates the desired state.

**Key Concepts**:
- **Providers**: Plugins to interact with cloud platforms (e.g., AWS).
- **Resources**: Infrastructure components (e.g., `aws_s3_bucket`).
- **Modules**: Reusable groups of resources.
- **State**: A snapshot (`terraform.tfstate`) of current infrastructure mapping.
- **Plan & Apply**: Workflow to preview and enact changes.

---

## 2. Installation & Setup

1. **Install Terraform**:
   ```bash
   # macOS (Homebrew)
   brew tap hashicorp/tap
   brew install hashicorp/tap/terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.5.6/terraform_1.5.6_linux_amd64.zip
   unzip terraform_1.5.6_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```
2. **Configure AWS CLI** (Terraform uses AWS credentials):
   ```bash
   aws configure
   # Provide AWS Access Key, Secret Key, region, output format
   ```

---

## 3. Core Terraform Commands

| Command             | Description                                                            |
|---------------------|------------------------------------------------------------------------|
| `terraform init`    | Initialize working directory, download providers and modules.          |
| `terraform validate`| Validate configuration syntax.                                         |
| `terraform plan`    | Show changes required to reach desired state.                          |
| `terraform apply`   | Apply the planned changes to reach desired state.                      |
| `terraform destroy` | Destroy all managed infrastructure.                                    |
| `terraform fmt`     | Format code according to best practices.                               |
| `terraform import`  | Import existing infrastructure into state.                             |
| `terraform state`   | Advanced state management (list, rm, mv, pull, push).                 |
| `terraform taint`   | Mark resource for recreation on next apply.                            |

---

## 4. Example: New AWS Project

### 4.1. Basic S3 Bucket

```hcl
provider "aws" {
  region = "us-west-2"
}

resource "aws_s3_bucket" "example" {
  bucket = "my-unique-bucket-name-123"
  acl    = "private"

  tags = {
    Name        = "ExampleBucket"
    Environment = "Dev"
  }
}
```  
**Commands**:
```bash
terraform init     # Initialize
terraform plan     # Review changes
terraform apply    # Create bucket
```  

### 4.2. EC2 Instance with Security Group

```hcl
resource "aws_security_group" "web_sg" {
  name = "web-sg"
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  security_groups = [aws_security_group.web_sg.name]

  tags = {
    Name = "WebServer"
  }
}
```  

---

## 5. Example: Managing Existing AWS Resources

### 5.1. Importing Resources

Import an existing S3 bucket:
```bash
terraform import aws_s3_bucket.example existing-bucket-name
```  
After import, add the matching `resource` block in `.tf`.

### 5.2. State Inspection & Manipulation

- **List resources in state**:
  ```bash
  terraform state list
  ```
- **Remove resource** (without destroying it):
  ```bash
  terraform state rm aws_s3_bucket.example
  ```
- **Move resource** (refactor names):
  ```bash
  terraform state mv aws_instance.old aws_instance.new
  ```

### 5.3. Forcing Recreation

Mark a resource as tainted to recreate:
```bash
terraform taint aws_instance.web
terraform apply
```  

---

## 6. State & Backend Best Practices

- **Remote Backend**: Store state remotely (e.g., S3 + DynamoDB for locking).
  ```hcl
  terraform {
    backend "s3" {
      bucket         = "terraform-state-bucket"
      key            = "project/terraform.tfstate"
      region         = "us-west-2"
      dynamodb_table = "terraform-locks"
      encrypt        = true
    }
  }
  ```
- **State Locking**: Prevent concurrent writes via DynamoDB.
- **Terraform Cloud/Enterprise**: Offers remote runs, team collaboration.

---

## 7. Modules & Reusability

- Use **modules** to encapsulate resource patterns.
- Example folder structure:
  ```
  modules/
    network/
      main.tf
      outputs.tf
    compute/
      main.tf
      outputs.tf
  main.tf
  variables.tf
  outputs.tf
  ```
- **Call module**:
  ```hcl
  module "network" {
    source = "./modules/network"
    vpc_cidr = "10.0.0.0/16"
  }
  ```

---

## 8. Workspaces & Environments

- **Workspaces** allow multiple state instances (e.g., dev, prod).
  ```bash
  terraform workspace new dev
  terraform workspace select prod
  terraform plan
  ```
- Keep variables in `*.tfvars` per environment.

---

## 9. Security & Compliance Best Practices

- **Use least privilege IAM roles** for Terraform execution.
- **Encrypt state** at rest and in transit.
- **Store secrets** in Vault or AWS Secrets Manager, not in code.

---

## 10. Architecture Diagram

```mermaid
graph LR
  A[Terraform CLI] --> B[Remote Backend (S3 + DynamoDB)]
  A --> C[AWS Provider]
  C --> D[VPC]
  C --> E[EC2]
  C --> F[S3]
  C --> G[Security Group]
```
*Figure: Terraform workflow with AWS provider and remote backend.*

---

## 11. References & Further Reading

- Terraform Official Docs: https://www.terraform.io/docs
- AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest
- Terraform Best Practices: https://www.terraform-best-practices.com

---

*End of guide.*