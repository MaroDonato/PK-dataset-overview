# An overview of human pharmacokinetic databases

Code and data for comparing publicly available human pharmacokinetic (PK) databases:

* `overview.ipynb`: generates overlap UpSetPlot and overview table
* `tsne.ipynb`: plots the chemical space of every database
* `requirements.txt`: lists the needed packages, run `pip install -r requirements.txt`

Run `overview.ipynb` before `tsne.ipynb`.

## Plots
Generated png and pdf files are in `plots` directory.

![Database_overlap.png](plots/Database_overlap.png)
UpSetPlot showing overlap between databases

![tSNE_chemical_space.png](plots/tSNE_chemical_space.png)
Overview of chemical space of databases vs ChEMBL Ro5 compounds.

![tSNE_bioavailability.png](plots/tSNE_bioavailability.png)
Overview of chemical space of compounds with bioavailability data vs ChEMBL Ro5 compounds.

## Table
| Dataset         | Vss  | CLplasma | CLint | CLhepatic | CLrenal | Fu   | t1/2 | PPB  | F    | logP | Total |
| :-------------- | :--- | :------- | :---- | :-------- | :------ | :--- | :--- | :--- | :--- | :--- | :---- |
| Paixão et al.   |      | 164      |       | 164       |         |      |      | 164  | 164  |      | 164   |
| Adachi et al.   | 365  |          | 365   | 365       | 365     | 365  |      |      |      | 365  | 365   |
| Lombardo et al. | 1315 | 1350     |       |           |         | 920  | 1335 |      |      |      | 1352  |
| e-Drug3D*       | 1109 | 1080     |       |           |         |      | 1475 | 1262 | 588  |      | 2083  |
*e-Drug3D database contains multiple PK values for the same CAS # for some compounds, leading to a higher total count.
