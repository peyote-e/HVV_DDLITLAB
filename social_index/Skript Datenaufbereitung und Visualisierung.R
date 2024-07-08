
################################################################################
###                                                                          ###
###                               HVV-Projekt                                ### 
###                                                                          ###
################################################################################



# Vorbereitung -----------------------------------------------------------------

options(scipen = 999) # Wissenschaftliche Schreibweise


## Paktete laden ---------------------------------------------------------------

library(tidyverse)  # Datenaufbereitung, Visualisierung, ...
library(here)       # Einlesen Haltestellendaten
library(readxl)     # Einlesen Daten Statistikamt
library(geojsonio)  # Einlesen statistische Gebiete
library(sf)         # Einlesen Geodaten Openstreetmap/ Haltestellendaten
library(psych)      # Cornbachs Alpha für Indizes



## Einlesen der Daten ----------------------------------------------------------


## Geodaten Statistische Gebiete

StatGebiete_geo <- geojson_read("Daten/StatGebieteHa/app_statistische_gebiete_EPSG_4326.json", what = "sp")


## Geodaten Haltestellen HVV

HVV <- st_read(here('Daten',
                    'HVV',
                    'Haltepunkte_2023.shp'))


## soziodemographische Daten statistische Bereiche

SbProfil <- read_excel("Daten/Statistikamt/Stadtteildaten Hamburg.xlsx", skip = 2, n_max = 943)


## soziodemographische Daten Stadtteile

StProfil <- read_excel("Daten/Statistikamt/Stadtteildaten Hamburg.xlsx", range = cell_rows(951:1050))



# Aufbereiten der Datensätze ---------------------------------------------------



## GEODATEN STATISTISCHE GEBIETE -----------------------------------------------


### Umwandeln in sf-Datensatz
StatGebiete_geo <- st_as_sf(StatGebiete_geo)

### Entfernen von Neuwerk und anderem komischen Bereich
StatGebiete_geo <- StatGebiete_geo[StatGebiete_geo$statgebiet != 106001, ]                  # Seeleute/Binnenschiffer
StatGebiete_geo <- StatGebiete_geo[StatGebiete_geo$statgebiet != 105001, ]                  # Neuwerk
StatGebiete_geo <- StatGebiete_geo[StatGebiete_geo$id != "APP_STATISTISCHE_GEBIETE_734", ]  # Hamburger Exklave "Volksdorfer Buschwiese"

StatGebiete_geo <- StatGebiete_geo |>
    rename(StatGebiet = statgebiet) |>
    mutate(StatGebiet = as.numeric(StatGebiet)) |>
    select(StatGebiet, geometry)


## GEODATEN HALTESTELLEN HVV ---------------------------------------------------


### Koordinatenbezugssysteme beider Datensätze miteinander kompatibel machen
HVV <- st_transform(HVV, crs = st_crs(StatGebiete_geo))

### Datensätze miteinander verbinden
HVV <- st_join(HVV, StatGebiete_geo)

### Haltestellen löschen, die nicht in Hamburg liegen
HVV <- HVV |> 
    filter(!is.na(StatGebiet))

### Art der Haltestelle codieren 

HVV <- HVV |>
    mutate(Hst = case_when(
        grepl("S$", NAME) ~ "S-Bahn",
        grepl("S11$", NAME) ~ "S-Bahn",
        grepl("U$", NAME) ~ "U-Bahn",
        grepl("U1$", NAME) ~ "U-Bahn",
        grepl("U4$", NAME) ~ "U-Bahn",
        grepl("U3$", NAME) ~ "U-Bahn",
        
        grepl("S2/S21$", NAME) ~ "S-Bahn", 
        grepl("AS$", CODE) ~ "S-Bahn", 
        grepl("HS$", CODE) ~ "S-Bahn", 
        grepl("U2$", NAME) ~ "U-Bahn", 
        grepl("U Süd$", NAME) ~ "U-Bahn",
        grepl("U Nord$", NAME) ~ "U-Bahn",
        grepl("U Ri. Süd$", NAME) ~ "U-Bahn",
        grepl("U Ri. Nord$", NAME) ~ "U-Bahn",
        grepl("Ri. Ost$", NAME) ~ "U-Bahn",
        grepl("Ri. West$", NAME) ~ "U-Bahn",
        grepl("BA$", CODE) ~ "U-Bahn",
        
        grepl("SLS$", CODE) ~ "AKN",
        grepl("ENZ$", CODE) ~ "AKN",
        grepl("BWD$", CODE) ~ "AKN",
        
        grepl("AWN$", CODE) ~ "RE",
        grepl("ARAL$", CODE) ~ "RE",
        grepl("AOW$", CODE) ~ "RE",
        grepl("AHSB$", CODE) ~ "RE",
        grepl("ABG$", CODE) ~ "RE",
        grepl("ADF$", CODE) ~ "RE",
        grepl("AA$", CODE) ~ "RE",
        grepl("AH$", CODE) ~ "RE",
        grepl("AHAR$", CODE) ~ "RE",
        
        TRUE ~ NA_character_))
  # |>
  #   filter(Hst != "AKN" | 
  #         Hst != "RE")


## DATEN STADTTEILE STATISTIKAMT -----------------------------------------------


StProfil <- StProfil |>
    rename(Stadtteil = ...1,
           Anteil_Migranten = ...18,
           Anteil_Alleinerziehende = ...28,
           Anteil_Aufstockerrentner = ...56,
           Anteil_Arbeitslose = ...48,
           Anteil_Autos = ...63)  |>
    mutate(Anteil_Migranten = as.numeric(Anteil_Migranten),
           Anteil_Alleinerziehende = as.numeric(Anteil_Alleinerziehende),
           Anteil_Aufstockerrentner = as.numeric(Anteil_Aufstockerrentner),
           Anteil_Arbeitslose = as.numeric(Anteil_Arbeitslose),
           Anteil_Autos = as.numeric(Anteil_Autos)) |>
    select(Stadtteil, Anteil_Migranten, Anteil_Alleinerziehende, Anteil_Aufstockerrentner, Anteil_Arbeitslose, Anteil_Autos) 


Dup1 <- StProfil |>
    slice(rep(which(Stadtteil == "Neuland/Gut Moor"), each = 2)) |>
    mutate(Stadtteil = c("Neuland", "Gut Moor")) |>
    filter(Stadtteil == "Neuland" | Stadtteil == "Gut Moor")

Dup2 <- StProfil |>
    slice(rep(which(Stadtteil == "Moorburg/Altenwerder"), each = 2)) |>
    mutate(Stadtteil = c("Moorburg", "Altenwerder")) |>
    filter(Stadtteil == "Moorburg" | Stadtteil == "Altenwerder")

Dup3 <- StProfil |>
    slice(rep(which(Stadtteil == "Waltershof/Finkenwerder"), each = 2)) |>
    mutate(Stadtteil = c("Waltershof", "Finkenwerder")) |>
    filter(Stadtteil == "Waltershof" | Stadtteil == "Finkenwerder")

Dup4 <- StProfil |>
    slice(rep(which(Stadtteil == "Steinwerder/Kl. Grasbrook"), each = 2)) |>
    mutate(Stadtteil = c("Steinwerder", "Kleiner Grasbrook")) |>
    filter(Stadtteil == "Steinwerder" | Stadtteil == "Kleiner Grasbrook")


StProfil <- rbind(StProfil, Dup1, Dup2, Dup3, Dup4)
rm(Dup1, Dup2, Dup3, Dup4)
StProfil <- StProfil|>
    filter(Stadtteil != "Neuland/Gut Moor" &
           Stadtteil != "Moorburg/Altenwerder" &
           Stadtteil != "Waltershof/Finkenwerder" &
           Stadtteil != "Steinwerder/Kl. Grasbrook")


## DATEN STATISTISCHE BEREICHE STATISTIKAMT ------------------------------------


### Umbenennung Spalten, Entfernen von NA´s, Entfernung von Dubletten

SbProfil <- SbProfil |>
    rename(StatGebiet =`Statistisches Gebiet`,
           Bruttofläche_ha = `Bruttofläche in ha`,
           Anteil_Migranten = `Anteil der Bevölkerung mit Migrations-hintergrund2`,
           Anteil_Alleinerziehende = `Anteil der Alleiner-ziehenden an allen Haushalten mit Kindern`,
           Anteil_Aufstockerrentner = `Anteil an der Bevölkerung 65 Jahre und älter`,
           Anteil_Arbeitslose = `Anteil an der Bevölkerung im erwerbs-fähigen Alter von 15 bis u. 65 Jahren`,
           Anteil_Autos = `Private          PKW                          je 1000 Einwohner`)|>
    mutate(Bruttofläche_ha = as.numeric(Bruttofläche_ha),
           Anteil_Migranten = as.numeric(Anteil_Migranten),
           Anteil_Alleinerziehende = as.numeric(Anteil_Alleinerziehende),
           Anteil_Aufstockerrentner = as.numeric(Anteil_Aufstockerrentner),
           Anteil_Arbeitslose = as.numeric(Anteil_Arbeitslose),
           Anteil_Autos = as.numeric(Anteil_Autos)) |>
    filter(!is.na(Stadtteil)) |>
    select(StatGebiet, Stadtteil, Bruttofläche_ha, 
           Anteil_Migranten, Anteil_Alleinerziehende, Anteil_Aufstockerrentner, 
           Anteil_Arbeitslose, Anteil_Autos) 


SbProfil <- SbProfil |>
    mutate(Elbe = ifelse(Stadtteil %in% c("Cranz", "Finkenwerder", "Neuenfelde", "Francop",
                                      "Neugraben-Fischbek", "Welterhof", "Altenwerder",
                                      "Moorburg", "Hausbruch", "Steinwerder", "Kleiner Grasbrook",
                                      "Heimfeld", "Eißendorf", "Harburg", "Neuland", "Wilstorf",
                                      "Gut Moor", "Marmstorf", "Langenbek", "Rönneburg", "Sinstorf",
                                      "Veddel", "Wilhelmsburg", "Waltershof"), 0, 1),
           Zentrum = ifelse(Stadtteil %in% c("Altona-Altstadt", "Altona-Nord", "Eimsbüttel",
                                             "Hoheluft-West", "Hoheluft-Ost", "Eppendorf",
                                             "Winterhude", "Barmbek-Süd", "Uhlenhorst",
                                             "Eilbek", "Hamm",  "HafenCity", "Harvestehude",
                                             "Hammerbrook", "Borgfelde", "Hohenfelde",
                                             "St.Georg", "Hamburg-Altstadt", "Neustadt",
                                             "St.Pauli", "Sternschanze","Rotherbaum"), 1, 0))


    
    
### Imputation 


#### Vorselektion nach bewohnten und unbewohnten Bereichen

unbewohnte_Bereiche <- SbProfil |>
    filter(is.na(Anteil_Migranten) & is.na(Anteil_Alleinerziehende) & 
           is.na(Anteil_Aufstockerrentner) & is.na(Anteil_Arbeitslose))

SbProfil <- SbProfil |>
    filter(!is.na(Anteil_Migranten) | !is.na(Anteil_Alleinerziehende) |
           !is.na(Anteil_Aufstockerrentner) | !is.na(Anteil_Arbeitslose))


#### Durchführung der Imputation

SbProfil <- SbProfil |>
    left_join(StProfil, by = "Stadtteil", suffix = c("_SbProfil", "_StProfil")) |>
    mutate(
        Anteil_Migranten = ifelse(is.na(Anteil_Migranten_SbProfil), 
                                  Anteil_Migranten_StProfil, Anteil_Migranten_SbProfil),
        Anteil_Alleinerziehende = ifelse(is.na(Anteil_Alleinerziehende_SbProfil), 
                                         Anteil_Alleinerziehende_StProfil, Anteil_Alleinerziehende_SbProfil),
        Anteil_Aufstockerrentner = ifelse(is.na(Anteil_Aufstockerrentner_SbProfil), 
                                          Anteil_Aufstockerrentner_StProfil, Anteil_Aufstockerrentner_SbProfil),
        Anteil_Arbeitslose = ifelse(is.na(Anteil_Arbeitslose_SbProfil), 
                                    Anteil_Arbeitslose_StProfil, Anteil_Arbeitslose_SbProfil),
        Anteil_Autos = ifelse(is.na(Anteil_Autos_SbProfil), 
                              Anteil_Autos_StProfil, Anteil_Autos_SbProfil)) |> 
    select(StatGebiet, Stadtteil, Bruttofläche_ha, Anteil_Migranten, 
           Anteil_Alleinerziehende, Anteil_Aufstockerrentner, Anteil_Arbeitslose, 
           Anteil_Autos, Elbe, Zentrum)
rm(StProfil)


#### Zusammenführten von imputiert bewohnten und unimputiert undbewohnten Bezirken

SbProfil <- rbind(SbProfil, unbewohnte_Bereiche)
rm(unbewohnte_Bereiche)



### Indexbildung 

SbProfil <- SbProfil |>
    rowwise() |>
    mutate(Armut = mean( c(Anteil_Alleinerziehende,
                           Anteil_Aufstockerrentner,
                           Anteil_Arbeitslose), na.rm = TRUE)) |>
    mutate(Indexvariable = mean( c(Anteil_Migranten, 
                                   Armut), na.rm = TRUE)) |>
    ungroup() 


## Reliabilitätscheck

Variablen_Alpha <- SbProfil |>
    select(Anteil_Alleinerziehende, Anteil_Aufstockerrentner, Anteil_Arbeitslose) |>
    st_drop_geometry()
print(alpha(Variablen_Alpha))
rm(Variablen_Alpha)



# Datensätze SbProfil und StatGebiete_geo zusammenfügen ------------------------


SbProfil <- inner_join(StatGebiete_geo, SbProfil, by= "StatGebiet")
rm(StatGebiete_geo)




#  Visualisierung --------------------------------------------------------------


## Statitische Gebiete
ggplot() +
    geom_sf(data = SbProfil, fill = "lightblue") +
    theme_minimal()


## Statistische Gebiete mit Haltestellen
ggplot() +
    geom_sf(data = SbProfil, fill = "lightblue") +
    geom_sf(data = HVV, color = "red", size = 0.2) +
    theme_minimal()


## Elbe
ggplot() +
    geom_sf(data = SbProfil, fill = "gray", color = "darkgray") +
    geom_sf(data = SbProfil |> filter(Elbe == 0), fill = "coral") +
    theme_minimal()

## Zentrum
ggplot() +
    geom_sf(data = SbProfil, fill = "gray", color = "darkgray") +
    geom_sf(data = SbProfil |> filter(Zentrum == 1), fill = "coral") +
    theme_minimal()

## Große Flächen
ggplot() +
    geom_sf(data = SbProfil, fill = "lightblue") +
    geom_sf(data = SbProfil |> filter(Bruttofläche_ha > 1000), color = "red") +
    theme_minimal()

# Histogramm Gesamtindex
ggplot(SbProfil, aes(x = Indexvariable)) +
    geom_histogram(binwidth = 1, fill = "skyblue", color = "black", aes(y = ..count..)) +
    labs(title = "Histogramm der Indexvariable", x = "Indexvariable", y = "Häufigkeit") +
    theme_minimal()

# Statistische Gebiete mit Armutsindex
SbProfil |>
    ggplot() +
    geom_sf(aes(fill = Armut ), color = "black") +
    scale_fill_gradient(low = "yellow", high = "red") +
    labs(fill = "Indexvariable\nArmut") +
    theme_minimal()


# Statistische Gebiete mit Gesamtindex
SbProfil |>
    ggplot() +
    geom_sf(aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "lightgreen", high = "darkgreen") +
    labs(fill = "Indexvariable\nGesamt") +
    theme_minimal()







# Validitätsprüfung Diskriminierungsindex --------------------------------------


## Geodaten Sozialmonitor

Sozialmonitor_geo <- geojson_read("Daten/Sozialmonitor/de_hh_up_sozialmonitoring_2020_EPSG_4326.json", what = "sp")
Sozialmonitor_geo <- st_as_sf(Sozialmonitor_geo)

ggplot() +
    geom_sf(data = Sozialmonitor_geo)

ggplot() +
    geom_sf(data = SbProfil, aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "white", high = "black")


# Niedrig

ggplot() +
    geom_sf(data = SbProfil, aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "white", high = "black") +
    labs(fill = "Indexvariable\nGesamt") +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "sehr niedrig"),
            fill = "red", colour = "red", alpha = 0.2) +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "niedrig"),
            fill = "orange", colour = "orange", alpha = 0.2) +
    theme_minimal()


# mittel

ggplot() +
    geom_sf(data = SbProfil, aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "white", high = "black") +
    labs(fill = "Indexvariable\nGesamt") +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "mittel"),
            fill = "blue", colour = "blue", alpha = 0.2) +
    theme_minimal()


# Hoch

ggplot() +
    geom_sf(data = SbProfil, aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "white", high = "black") +
    labs(fill = "Indexvariable\nGesamt") +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "hoch"),
            fill = "lightgreen", colour = "lightgreen", alpha = 0.2) +
    theme_minimal()


# Alle

ggplot() +
    geom_sf(data = SbProfil, aes(fill = Indexvariable ), color = "black") +
    scale_fill_gradient(low = "white", high = "black") +
    labs(fill = "Indexvariable\nGesamt") +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "sehr niedrig"),
            fill = "red", colour = "red", alpha = 0.2) +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "niedrig"),
            fill = "orange", colour = "orange", alpha = 0.2) +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "mittel"),
            fill = "blue", colour = "blue", alpha = 0.2) +
    geom_sf(data = Sozialmonitor_geo |> filter(statusindex == "hoch"),
            fill = "lightgreen", colour = "lightgreen", alpha = 0.2) +
    theme_minimal()



# Visualisierung der Imputationsgebiete

## Plot muss vor der Imputation durchgeführt werden !

ggplot() +
    geom_sf(data = SbProfil, fill = "lightblue") +
    geom_sf(data = SbProfil %>% filter(is.na(Anteil_Migranten)), fill = "red", alpha = 0.33) +
    geom_sf(data = SbProfil %>% filter(is.na(Anteil_Alleinerziehende)), fill = "red", alpha = 0.33) +
    geom_sf(data = SbProfil %>% filter(is.na(Anteil_Aufstockerrentner)), fill = "red", alpha = 0.33) +
    geom_sf(data = SbProfil %>% filter(is.na(Anteil_Arbeitslose)), fill = "red", alpha = 0.33) +
    geom_sf(data = SbProfil %>% filter(is.na(Anteil_Migranten) & is.na(Anteil_Alleinerziehende) & 
                                           is.na(Anteil_Aufstockerrentner) & is.na(Anteil_Arbeitslose)), 
            fill = "darkgray") +
    theme_minimal()
