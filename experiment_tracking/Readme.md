# Experiment Tracking

## Description du projet
Je suis Data engineer spécialisé ELT/ETL et business analytics depuis 3 ans, je m'oriente en Machine learning Operations / IA Engineer.
Ce projet vise à démontrer mes compétences en **`experiment tracking`** au vue d'une candidature.

Il démontre mes expertises en :
- Déploiement automatisé d'un serveur d'*experiment tracking* dans le cloud avec **MLflow**.
- Ingestion normalisée de données.
- Mise en place d'outils intuitifs pour les data scientists : `WebApp`, commandes `make`, et gestion de secrets.
- Configuration, déploiement et utilisation de **MLflow** dans un contexte de data science.
- Devops : AWS DevOps / CloudFormation 


Pour plus de contexte sur mon parcours, consultez la section "Qui suis-je ?" en fin de ce README.

## Objectif du Projet

Ce projet vise à illustrer un flux complet d'*experiment tracking* en MLOps, en simulant un environnement de production où plusieurs data scientists travaillent ensemble. 

Chaque data scientist est en mesure de : 
- Déployer la stack
- Ingérer les données en une commande
- Développer des scripts d'entrainement
- Entrainer les modéles
- Tracker l'avancement global du projet **via une interface web**. 
## Structure du projet

Le projet est composé des éléments suivants :
- Une instance virtuelle sur **AWS EC2** pour héberger le serveur de `MlFlow`.
- Une base de données **PostgreSQL** sur **AWS RDS** pour stocker les métadonnées des expériences.
- Un module local d'ingestion de données, normalisant les datasets pour l'entraînement.
- Un module d'entraînement de modèles ML, intégrant **MLflow** pour le logging.
- Une WebApp de tracking basée sur **FastAPI**, dédiée aux data scientists pour visualiser et interagir avec les expériences en temps réel.
  
![alt text](experiment_tracking/readme_images/global_project.png)

### Screenshots 

**Stack déployée**
![alt text](experiment_tracking/readme_images/cloud_formation.png)

**connexion au EC2**
![alt text](experiment_tracking/readme_images/connect_ec2.png)

**Ingestion**
![alt text](experiment_tracking/readme_images/ingestion.png)

**Training**
![alt text](experiment_tracking/readme_images/training.png)

**Tracker / runs data**
![alt text](experiment_tracking/readme_images/tracker_1.png)

**Tracker / datasource**
![alt text](experiment_tracking/readme_images/tracker_2.png)


## Repository:
```bash
  .
  ├── experiment_tracking
  │   ├── .env                                   # Fichier d'environnement a rajouter manuellement, voir template plus bas. 
  │   ├── infra                                  # Fichiers de DevOps
  │   │   ├── config.toml
  │   │   ├── ec2-init.sh
  │   │   └── template.yaml
  │   ├── ingestion                              # Scriptes d'ingestion
  │   │   ├── ingest.py
  │   │   ├── iris.py
  │   │   └── utils.py        
  │   ├── __init__.py                             # Initialise le module
  │   ├── Makefile                                # Contient les commandes d'automatisation
  │   ├── readme_images                           # Propre au Readme
  │   │   ├── ...
  │   ├── secret                                  # A rajouter manuellement
  │   │   └── Keyname.pem
  │   ├── training                                # Scriptes d'entrainement (N'étant pas Data scientist, les scriptes sont triviaux)
  │   │   ├── train_iris_classification.py
  │   │   └── utils.py
  │   └── webapp                                  # WebApp sur FastApi
  │       ├── app.py
  │       ├── __init__.py
  │       ├── sql                                 # Les endpoints de l'API (1 requête = 1 endpoint)
  │       │   ├── artifacts.sql
  │       │   ├── data_sources.sql
  │       │   └── runs.sql
  │       └── utils.py
  ├── Readme.md
  └── requirements.txt                            # Librairies python

```

## Quick start

### Prérequis
Avant de lancer le tracking il vous faut : 
- Un port libre sur votre machine example: `8000` pour la web app. vous le metterez ensuite dans la variable `$WEBAPP_PORT`
- Une base de donnée RDS dont vous connaissez le `host` `username` et `password`
- Les ressources AWS suivantes
  
| Ressource            | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| AWS client `awsv2`   | Client AWS installé et accessible via `awsv2` (version définie dans requirements.txt). |
| `$INFRA_BUCKET`      | Bucket S3 utilisé par AWS SAM.                                              |
| `$ARTIFACTS_BUCKET`  | Bucket S3 destiné au stockage des artifacts.                                |
| Subnet ID            | Identifiant d’un subnet relié au VPC par défaut (ex. `subnet-1234frt5653`). |
| Security Group ID    | Identifiant d’un security group (ex. `sg-1234frt5653`).                     |
| EC2 Key Pair         | Clé EC2 enregistrée dans `./experiment_tracking/secret/$KEYNAME`.           |

  
### Configuration du Security group de l'EC2 et de la base de donnée

#### Security group : EC2
Son ID est défini dans la variable `$EC2_SECURITY_GROUP` _par example `sg-0c439c4ee075e16b6`_

Il n'est pas créé par cloudformation car je préfére les security groups dynamiques si on souhaite plus tard changer de régles, ajouter ou filtrer des adresses IP etc..

**inbound rules** : Agents extérieurs qui peuvent avoir accés à l'EC2 en dehors de son réseau local.
| Type | Port | IP Range | Description |
|------|------|----------|-------------|
| SSH  | 22   | Votre adresse IP | Permet à `make connect_ec2` de se connecter à la machine virtuelle via SSH en utilisant `./secret/$KEYNAME` |
| TCP  | 5000 | Votre adresse IP | Permet à votre adresse IP de se connecter au webserver de MLFlow |

**outbound rules** : A quoi peut avoir accés l'EC2 en dehors de son réseau local.
Donne un accés extérieur à l'EC2
| Type |IP Range | Description |
|------|---------|-------------|
|HTTP|0.0.0.0/0 | Donne un accés internet à l'EC2 pour DL les librairies et accéder à S3

#### Security group : RDS
La base de donnée existe *en dehors de cloudformation* pour des raisons de sécurité. Quoi qu'il arrive à la stack, les données sont persistés.

**inbound rules** : Qui peut requêter la base de donnée ?
| Type | Port | Source | Description |
|------|------|--------|-------------|
| TCP  | 5432 | `$EC2_SECURITY_GROUP` | Permet à l'EC2 (MLflow server) de se connecter à la BD  |
| TCP  | 5432 | Votre adresse IP | Optionel : Vous permet de vous connecter localement à la BD|


### Librairies Python
1- Dans un environnement virtuel sous **`python >= 3.8`**
```bash
    cd experiment_tracking
    pip install -r requirements.txt
```
2- Tester les commandes
```bash
    awsv2 --version
    sam --version
```
### Variables d'environnements
Créer un fichier dans `./experiment_tracking/.env` et le peupler suivant le template suivant:

**_Note : A ce stade, vous ne connaissez pas encore EC2_PUBLIC_URL car la machine virtuelle n'existe pas encore_**

```conf
    #----------------
    # EC2 publuc IP |
    #----------------
    # Update EC2 publuc IP each new deployement
    EC2_PUBLIC_URL=     # Example : "13.39.162.164"

    #---------
    # Python |
    #---------
    # Point to "bin/python3.n" (n>=8) of your virtual env 
    PYTHON_INTERPRETER_PATH=/path/to/virtual_env/bin/python3.11

    #-----------
    # Postgres |
    #-----------
    host=example-database.abcdefghijklmnop.eu-west-3.rds.amazonaws.com
    dbname=postgres
    user=your_user
    password=admin
    port=5432
    RDS_INGESTION_SCHEMA=ingestion_schema_name

    #--------
    # infra |
    #--------
    MLFLOW_VERSION=2.17.2                       # Fixed, do not change it.
    INFRA_BUCKET=some_bucket_name               # Bucket name where AWS SAM create the stack build
    ARTIFACTS_BUCKET=some_other_bucket_name     # Bucket name where MlFlow will save the artifacts
    SUBNET_ID=subnet-xxxx                       # Subnet in which the EC2 will be deployed 
    SECURITY_GROUP_IDS=sg-xxxx                  # Security group linked with the EC2 machine
    KEYNAME=some_key_pair_name                  # KeyName name under "./secret/KEYNAME"
    WEBAPP_PORT=8000                            # Local port where the FastApi webapp will run
```
# Run project

- Step 1 : Deploy Architecture
```bash
    make deploy_archi 
```
A la fin du run, La commande retourne l'IP publique de l'instance EC2. voir [screenshot](https://github.com/uzicorn/mlops/blob/main/experiment_tracking/readme_images/cloud_formation.png)
- Step 2 : Remplir `EC2_PUBLIC_URL` dans `./experiment_tracking/.env`
- Step 3 : Lancer l'ingestion
```bash
    make ingest
```
- step 4: Lancer l'entrainement des modèles
```bash
    make train_iris_ingestion
```
- step 5: Lancer la web app
```bash
    make run_webapp
```

Sur votre navigateur, allez sur : 

- **http://127.0.0.1:`$WEBAPP_PORT`/backend/runs**

- **http://127.0.0.1:`$WEBAPP_PORT`/backend/data_source**

# Specificités du projet

### Makefile
```yaml
### Makefile variables
WORKDIR: /path/to/mlops/experiment_tracking
ENVPATH: $(WORKDIR)/.env

### Infra 
build_sam: Build into infra/.aws-sam.  
deploy_sam: Deploy resources to the mlops-serverless CloudFormation stack.  
upload_init_script_to_s3: Resolve variables in infra/ec2-init.sh and upload to $INFRA_BUCKET/ec2-init.sh.  
deploy_infra: run upload_init_script_to_s3 -> build_sam -> deploy_sam.  

### Webapp
run_webapp: Run webapp in port $WEBAPP_PORT

### MLOps
connect_ec2: SSH to the EC2 instance using secret/$KEYNAME.  
ingest: Run ingestion.ingest.  
train_iris_classification`: Run training.train_iris_classification.  

### Cleanup
delete_mlflow_backend: Truncate MLflow backend tables in RDS.  
delete_mlflow_artifacts: Delete all artifacts in $ARTIFACTS_BUCKET. 
delete_mlflow_data: delete_mlflow_backend -> delete_mlflow_artifacts.  
hard-delete-stack: Delete the `mlops-serverless` stack and AWS SAM cache.  
clear_pycache`: Remove Python cache files.  
order66`: delete_mlflow_backend -> delete_mlflow_artifacts -> clear_pycache -> hard-delete-stack. 
```

### Ingestion (ELT)
- Le script d’ingestion crée des classes Python `Dataset`.
- Un `Dataset` est un ensemble de données d’entraînement et de test extrait d’une source brute, avec des attributs fixes :
  - name : `String`
  - training_data : `Dataframe`
  - test_data : `Dataframe`

- Pour chaque source, un script *connecteur* (ex : ingestion/iris.py) crée l’objet `Dataset` selon la spécification de la source, que ce soit un repo public, une API ou le résultat d'un scrapping.
- À chaque stockage dans l’entrepôt de données, la table `$RDS_INGESTION_SCHEMA.dataset_metadata` est complétée avec les métadonnées du `Dataset` :
  - Emplacement des tables train et test dans la base
  - Nom du dataset
  - Date d’ingestion  

L’objet `Dataset` garantit que *les données sont normalisées avant le stockage*.

**Exemple de connecteur** : ingestion/iris.py  
1. `iris.py` charge le dataset Iris depuis scikit-learn.  
2. Les colonnes sont renommées (ex : `sepal length (cm)` → `sepal_length_cm`).  
3. Les colonnes entières sont converties en `float64` pour la compatibilité MLflow.  
4. Deux splits train/test sont créés (80/20 et 75/25).  
5. `ingestion.py` appelle `load_data()` pour insérer les datasets et les métadonnées dans RDS.  

Tables générées dans le schéma `mlops_schema` :  
- `iris_0_train`, `iris_0_test` (split 80/20)  
- `iris_1_train`, `iris_1_test` (split 75/25)  

### Entraînement
`train_iris_classification.py` :
1. Charge les datasets train/test depuis RDS.  
2. Configure MLflow : niveau de log, URI du serveur de tracking (depuis `./experiment_tracking/.env`) et nom de l’expérience.  
3. Vérifie qu’aucun run n’est actif avant d’en démarrer un nouveau pour éviter les conflits.  
4. Appelle la fonction générique `utils.classification_training` avec :  
   - `model_name` : nom de l’artifact enregistré dans `s3://$ARTIFACTS_BUCKET/<run_id>/<model_name>`.  
   - `train_df` / `test_df` : DataFrames chargés depuis `$RDS_INGESTION_SCHEMA`.  
   - `param_dict` : paramètres scikit.  
   - `target_column` : colonne label.  
5. Entraîne, évalue et log les métriques ; sauvegarde les artifacts dans `$ARTIFACTS_BUCKET` si l’accuracy > 0.8.

### Gestion des secrets sur le cloud
L'initialisation de la machine virtuelle EC2 nécessite des variables de connexion à la base de donnée. 

J'ai profité du POC pour implémenter une idée qu'il ne m'aurait pas été possible de faire en production. 

Voir la documentation de l'implémentation sur `infra/ec2-init.sh`

## ça marche pas !

### Problémes fréquents 

A- Avez vous activé votre environnement virtuel ? `source /path/to/virtuel_env/bin/activate`

B- La commande `make train_iris_clasification` freeze : Avez vous copié la valeur de `$EC2_PUBLIC_URL` dans le .env après le deploiement ?

C- **Problèmes liés au réseau**

- Le serveur EC2 n’est pas accessible via **http://`$EC2_PUBLIC_URL`:5000/#/**

    - **Cas 1 : Impossible de se connecter à l’EC2 avec `make connect_ec2`**  
      → Vérifier que votre adresse IP est bien autorisée dans le security group de l’EC2 pour le port 22  
        (voir **security groups / EC2 / inbound_rules**).

    - **Cas 2 : Connexion SSH OK, mais rien ne tourne sur le port 5000 (serveur MLflow)**  
        - Vérifier que MLflow est installé :  
          ```bash
            mlflow --version
          ```
            - **Si MLflow est installé** :  
              L’EC2 n’a probablement pas accès à la base de données.  
              Vérifier que le security group de l’EC2 est bien autorisé dans l’inbound rule du RDS pour le port 5432  
              (voir **security groups / RDS / inbound_rules**).

            - **Si MLflow n’est pas installé** :  
              Vérifier que `ec2-init.sh` est présent :  
              ```bash
              cat ../../ec2-init.sh
              ```
              - S’il manque :  
                Le script n’a pas été récupéré depuis le bucket `$INFRA_BUCKET`.  
                Vérifier que l’EC2 possède une outbound rule lui permettant d’accéder à Internet (et donc au bucket S3).
                Faites tourner `make order66` puis refaire les étapes du chapitre Run project


## 👤 Author

ZENINI SALIM  
zenini.salim@gmail.com  
07 56 13 48 52
Created as a portfolio project to demonstrate MLOps fundamentals on MLflow and AWS.

ZENINI SALIM
