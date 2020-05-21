import 'leaflet';
import * as d3s from 'd3-selection';
import dataset from '../../conf/dataset.json';

export const state = {
  polygons: [],
  source_images: [],
  pred_images: [],
  focus: null,
  mode: "create"
}

// needed to initiate the map
let groups = ["map", "controls"];
d3s.select("#root")
  .selectAll("div")
  .data(groups).enter()
  .append("div")
  .attr("id", (d) => d);

d3s.select("#map")
  .style("height", "500px")
  .style("width", "700px");

export let map = L.map("map", {
  zoomControl: false,
  crs: L.CRS.EPSG3857, // this is the projection CRS (EPSG:3857), but it is different than the data CRS (EPSG:4326). See https://gis.stackexchange.com/questions/225765/leaflet-map-crs-is-3857-but-coordinates-4326/225786.
  center: dataset.basemapLayer.initialLocation,
  zoom: dataset.basemapLayer.initialZoom,
  url: dataset.basemapLayer.url,
});

export let backendUrl = "http://localhost:4446/";
