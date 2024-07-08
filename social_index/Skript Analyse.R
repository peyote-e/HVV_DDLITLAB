################################################################################
###                                                                          ###
###                                    Analyse                               ###
###                                                                          ###
################################################################################


## Laden Pakete ----------------------------------------------------------------

library(tidyverse)
library(spdep)
library(spatialreg)
library(stargazer)


## Laden der AV-Daten ----------------------------------------------------------


Datensatz_Anbindung <- read.csv("Daten/stat_gebiet_flaeche_hvv_stops_bev_zahl_score2.csv", sep = ",")

Datensatz_Anbindung <- Datensatz_Anbindung |>
    select(statgebiet, log_index_hvv_angebotbev_anzahl) |>
    rename(StatGebiet = statgebiet,
           Anbindung = log_index_hvv_angebotbev_anzahl)

SbProfil <- SbProfil |>
    left_join(Datensatz_Anbindung, by= "StatGebiet")
rm(Datensatz_Anbindung)



## Löschen von Fällen ohne NA´s und aufsplitten der Datensätze -----------------


SbProfil_Gesamt <- SbProfil |>
    select(StatGebiet, Indexvariable, Anbindung, Anteil_Autos, Elbe, Zentrum, 
           Bruttofläche_ha, geometry) |>
    na.omit()

SbProfil_Zentrum <- SbProfil_Gesamt |>
    filter(Zentrum == 1)

SbProfil_Peripherie <- SbProfil_Gesamt |>
    filter(Zentrum == 0)



## Vorab-Test für Spatial Autokorrelation --------------------------------------


nb <- poly2nb(SbProfil_Gesamt, queen=TRUE)
lw <- nb2listw(nb, style="W", zero.policy=TRUE)
I <- moran(SbProfil_Gesamt$Indexvariable, lw, length(nb), Szero(lw))[1]

moran.test(SbProfil_Gesamt$Indexvariable,lw, alternative="greater")




## Gewichte für Spatial Regression festlegen -----------------------------------


nb_gesamt <- poly2nb(SbProfil_Gesamt, queen=TRUE)    
nb_gesamt_list <- nb2listw(nb_gesamt)                

nb_zentrum <- poly2nb(SbProfil_Zentrum, queen=TRUE) 
nb_zentrum_list <- nb2listw(nb_zentrum)

nb_peripherie  <- poly2nb(SbProfil_Peripherie, queen=TRUE) 
nb_peripherie_list <- nb2listw(nb_peripherie)



## Regressionsmodelle ----------------------------------------------------------


## Vorbereitung

Regressionsgleichung <- Anbindung ~ Indexvariable + Elbe + Zentrum + Anteil_Autos + Bruttofläche_ha
options(scipen = 7)


## Gesamtmodell

Gesamt_SEM <- errorsarlm(Regressionsgleichung, 
                         data = SbProfil_Gesamt, 
                         listw = nb_gesamt_list, 
                         zero.policy = TRUE)
summary(Gesamt_SEM)


## Modell Peripherie

Peripherie_SEM <- errorsarlm(Regressionsgleichung, 
                             data = SbProfil_Peripherie, 
                             listw = nb_peripherie_list, 
                             zero.policy = TRUE)
summary(Peripherie_SEM)


## Modell Zentrum

Zentrum_SEM <- errorsarlm(Regressionsgleichung, 
                          data = SbProfil_Zentrum, 
                          listw = nb_zentrum_list, 
                          zero.policy = TRUE)
summary(Zentrum_SEM)



## Testung Grundannahmen -------------------------------------------------------


# Lineare Beziehung

plot(fitted(Gesamt_SEM), residuals(Gesamt_SEM))
abline(h = 0, col = "red")


# Homoskedastizität

plot(fitted(Gesamt_SEM), residuals(Gesamt_SEM))
abline(h = 0, col = "red")


# Spatial Autokorrelation

nb <- poly2nb(SbProfil_Gesamt, queen=TRUE)
lw <- nb2listw(nb, style="W", zero.policy=TRUE)
I <- moran(SbProfil_Gesamt$Indexvariable, lw, length(nb), Szero(lw))[1]

moran.test(SbProfil_Gesamt$Indexvariable,lw, alternative="greater")


# Multikoliniarität

lm_model <- lm(Regressionsgleichung, data = SbProfil_Gesamt)
vif(lm_model)


# Normalverteilung der Fehler

hist(residuals(Gesamt_SEM), breaks = 20)



## Outputtabelle Regression ----------------------------------------------------

stargazer(Gesamt_SEM, Zentrum_SEM, Peripherie_SEM,
          type = "text",                                             # Art des Exports
          dep.var.caption  = "Anbindung an den HVV",                 # Überschrift der Gesamttabelle
          model.numbers = FALSE,                                     # Modellnummern ausblenden
          dep.var.labels.include = FALSE,                            # Gesamtüberschrift der Modelle ausblenden
          column.labels = c("Gesamt", "Zentrum", "Peripherie"),      # Modellüberschriften festlegen
          star.char = c("+", "*", "**", "***"),                      # Festlegung der Signifikanzsymbole
          star.cutoffs = c(.1, .05, .01, .001),                      # Festlegung der p-Werte für Signifikanzen
          notes.append = FALSE,                                      # Automatische Notizen ausblenden
          notes = c("+ p<0.1; * p<0.05; ** p<0.01; *** p<0.001"))    # Eigene Notizen einstellen


stargazer(Gesamt_SEM, Zentrum_SEM, Peripherie_SEM,
          type = "html",                                             # Art des Exports
          out = "Regressionsoutput/Output.html",
          dep.var.caption  = "Anbindung an den HVV",                 # Überschrift der Gesamttabelle
          model.numbers = FALSE,                                     # Modellnummern ausblenden
          dep.var.labels.include = FALSE,                            # Gesamtüberschrift der Modelle ausblenden
          column.labels = c("Gesamt", "Zentrum", "Peripherie"),      # Modellüberschriften festlegen
          star.char = c("+", "*", "**", "***"),                      # Festlegung der Signifikanzsymbole
          star.cutoffs = c(.1, .05, .01, .001),                      # Festlegung der p-Werte für Signifikanzen
          notes.append = FALSE,                                      # Automatische Notizen ausblenden
          notes = c("+ p<0.1; * p<0.05; ** p<0.01; *** p<0.001"))    # Eigene Notizen einstellen

stargazer(Gesamt_SEM, Zentrum_SEM, Peripherie_SEM,
          type = "latex",                                            # Art des Exports
          dep.var.caption  = "Anbindung an den HVV",                 # Überschrift der Gesamttabelle
          model.numbers = FALSE,                                     # Modellnummern ausblenden
          dep.var.labels.include = FALSE,                            # Gesamtüberschrift der Modelle ausblenden
          column.labels = c("Gesamt", "Zentrum", "Peripherie"),      # Modellüberschriften festlegen
          star.char = c("+", "*", "**", "***"),                      # Festlegung der Signifikanzsymbole
          star.cutoffs = c(.1, .05, .01, .001),                      # Festlegung der p-Werte für Signifikanzen
          notes.append = FALSE,                                      # Automatische Notizen ausblenden
          notes = c("$^{+}$p$<$0.1; 
                     $^{*}$p$<$0.05; 
                     $^{**}$p$<$0.01; 
                     $^{***}$p$<$0.001"))  



