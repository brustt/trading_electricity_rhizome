- créer un environnement : 
conda create -n <nom_env> python=3.9

a faire à chaque fois :
- activer l'env  
conda activate <nom_env>

- se placer dans le dossier /trading_electricity_rhizome

commande run : 

python src/main.py <arguments>

Les arguments sont (ne pas prendre en compte les guillemets): 

--market_name=<market_name>
Les valeurs possibles de <market_name>sont : "france", "germany" ou "uk"


--exp_name=<market_name>
Les valeurs possibles de <market_name>sont : "france", "germany" ou "uk"
