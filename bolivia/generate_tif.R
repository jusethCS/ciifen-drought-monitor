#!/usr/bin/Rscript

# Load required libraries
library(ggplot2)
library(gstat)
library(sp)
library(raster)
library(rgdal)

# Get command line arguments
args <- commandArgs(T)
FILEPATH = args[1]
OUTPATH = args[2]
XVAR = args[3]

# Load the drought data from the provided CSV file
sequia <- read.csv(file = FILEPATH, header = TRUE)
sequia <- sequia[, c("Lon", "Lat", XVAR)]
names(sequia) <- c("Lon", "Lat", "value")

# Copy the drought data and adjust coordinates
sequia2 <- sequia
sequia2$x <- sequia2$Lon   # Assign longitude to 'x'
sequia2$y <- sequia2$Lat   # Assign latitude to 'y'

# Convert to a spatial object
coordinates(sequia2) <- ~x + y
crs(sequia2) = "+proj=longlat +datum=WGS84 +no_defs"

# Define the coordinate range for the interpolation grid
x.range <- as.numeric(c(-73.75, -56.00))   # Longitude range
y.range <- as.numeric(c(-23.50, -9.00))      # Latitude range


# Create a grid with the specified coordinate range
grd <- expand.grid(x = seq(from = x.range[1], to = x.range[2], by = 0.25),
                   y = seq(from = y.range[1], to = y.range[2], by = 0.25))

# Convert the grid into a spatial object
coordinates(grd) <- ~x + y
gridded(grd) <- TRUE
crs(grd) = "+proj=longlat +datum=WGS84 +no_defs"

# Perform Inverse Distance Weighting (IDW) interpolation
idw <- idw(formula = value ~ 1, sequia2, newdata = grd)

# Convert IDW result into a data frame
idw.output <- as.data.frame(idw)
names(idw.output)[1:3] <- c("long", "lat", "sequia")  # Rename columns

# Load the contour shapefile for masking
est_contour <- rgdal::readOGR("assets", "bolivia")
est_contour <- fortify(est_contour)  # Convert for use with ggplot2

# Convert the IDW result into a raster object
idw.r <- rasterFromXYZ(idw.output[, c("long", "lat", "sequia")])

# Load the contour shapefile again for cropping
est_contour_k <- rgdal::readOGR("assets", "bolivia")

# Crop the raster using the contour shapefile
idw.crp <- crop(idw.r, est_contour_k)

# Mask the cropped raster using the contour shapefile
idw.msk <- mask(idw.crp, est_contour_k)

# Save the masked raster to the file specified in the third argument
writeRaster(idw.msk, OUTPATH, options = c('TFW=YES'), overwrite=TRUE)
