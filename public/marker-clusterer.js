/*
 * Copyright 2012 Naver Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @name MarkerClusterer
 * @namespace
 * @author Naver Labs
 */
(function(w) {
	/**
	 * Creates a new MarkerClusterer for the given map.
	 *
	 * @param {naver.maps.Map} map The map on which to cluster.
	 * @param {Array<naver.maps.Marker>=} opt_markers Optional markers to add to the cluster.
	 * @param {Object=} opt_options support 'minClusterSize', 'maxZoom', 'gridSize', 'styles', 'clusterIcon'
	 * @constructor
	 */
	var MarkerClusterer = function(map, opt_markers, opt_options) {
		// Public properties
		/**
		 * The map managed by the MarkerClusterer.
		 * @type {naver.maps.Map}
		 */
		this.map_ = map;

		/**
		 * The array of markers in the clusterer.
		 * @type {Array.<naver.maps.Marker>}
		 */
		this.markers_ = [];

		/**
		 * The array of MarkerCluster objects.
		 * @type {Array.<MarkerCluster>}
		 */
		this.clusters_ = [];

		/**
		 * The Google image path for the clusterer.
		 * @type {string}
		 */
		// this.imagePath_ = './images/m';

		/**
		 * The Google image extension for the clusterer.
		 * @type {string}
		 */
		// this.imageExtension_ = 'png';

		/**
		 * The grid size of the clusterer.
		 * @type {number}
		 * @private
		 */
		this.gridSize_ = 60; // 픽셀 단위

		/**
		 * The minimum number of markers to be in a cluster.
		 * @type {number}
		 * @private
		 */
		this.minClusterSize_ = 2; // 최소 2개부터 클러스터링

		/**
		 * The maximum zoom level that a marker can be clustered.
		 * @type {number}
		 * @private
		 */
		this.maxZoom_ = null; // 최대 줌 레벨 (이 이상은 클러스터링 안함)

		/**
		 * The styles for the clusterer.
		 * @type {Array.<Object>}
		 * @private
		 */
		this.styles_ = [];

		/**
		 * Whether the grid is used in the clusterer.
		 * @type {boolean}
		 * @private
		 */
		this.is=true;

		/**
		 * Whether the object is operating on markers.
		 * @type {boolean}
		 * @private
		 */
		this.ready_ = false;

		var options = opt_options || {};

		// Set the single properties if they exist in the options object.
		if (options['gridSize']) {
			this.gridSize_ = options['gridSize'];
		}
		if (options['minClusterSize']) {
			this.minClusterSize_ = options['minClusterSize'];
		}
		if (options['maxZoom']) {
			this.maxZoom_ = options['maxZoom'];
		}
		if (options['styles']) {
			this.styles_ = options['styles'];
		}
		if (options['clusterIcon']) {
			this.clusterIcon_ = options['clusterIcon'];
		}
		if (options['disableClickZoom']) {
			this.disableClickZoom_ = options['disableClickZoom'];
		}

		this.setupStyles_();

		this.prevZoom_ = this.map_.getZoom();

		this.bindEvents_();

		// Add the markers to the clusterer if the user specified them.
		opt_markers && this.addMarkers(opt_markers);

		this.ready_ = true;

	};

	// MarkerClusterer extends Naver.maps.OverlayView
	MarkerClusterer.prototype = new naver.maps.OverlayView();

	/**
	 * Binds the MarkerClusterer events.
	 * @private
	 */
	MarkerClusterer.prototype.bindEvents_ = function() {
		var that = this;

		// 마커 클러스터링 처리 관련 이벤트
		naver.maps.Event.addListener(this.map_, 'zoom_changed', function() {
			var zoom = that.map_.getZoom();
			var maxZoom = that.maxZoom_;
			var prevZoom = that.prevZoom_;

			if (zoom < prevZoom) { // 줌 아웃 시 클러스터링 다시 그림
				that.resetViewport();
			} else { // 줌 인 시 클러스터링 다시 그림
				that.redraw();
			}
			that.prevZoom_ = zoom;
		});

		naver.maps.Event.addListener(this.map_, 'idle', function() {
			that.redraw();
		});
	};

	/**
	 * Sets the styles an an array of objects with the following properties:
	 * url: (string) The URL for the image if the marker cluster is to be a picture.
	 * height: (number) The height of the image if the marker cluster is to be a picture.
	 * width: (number) The width of the image if the marker cluster is to be a picture.
	 * anchor: (Array<number, number>) The anchor position of the foreground image.
	 * textColor: (string) The text color of the initial number of markers in the cluster.
	 * textSize: (number) The text size of the initial number of markers in the cluster.
	 * backgroundPosition: (string) The background-position for the default clusterer icon.
	 *
	 * @param {Array<Object>} styles The style to set.
	 * @private
	 */
	MarkerClusterer.prototype.setupStyles_ = function() {
		if (this.styles_.length) {
			return;
		}

		for (var i = 1; i <= 5; i++) {
			this.styles_.push({
				url: this.imagePath_ + i + '.' + this.imageExtension_,
				height: 53,
				width: 53
			});
		}
	};

	/**
	 * Fit the map to the bounds of the markers in the clusterer.
	 */
	MarkerClusterer.prototype.fitMapToMarkers = function() {
		var markers = this.getMarkers();
		var bounds = new naver.maps.LatLngBounds();

		for (var i = 0, marker; marker = markers[i]; i++) {
			bounds.extend(marker.getPosition());
		}

		this.map_.fitBounds(bounds);
	};

	/**
	 * Sets the grid size of the clusterer
	 *
	 * @param {number} size The grid size of the clusterer.
	 */
	MarkerClusterer.prototype.setGridSize = function(size) {
		this.gridSize_ = size;
	};

	/**
	 * Returns the grid size of the clusterer
	 *
	 * @return {number} The grid size of the clusterer.
	 */
	MarkerClusterer.prototype.getGridSize = function() {
		return this.gridSize_;
	};

	/**
	 * Sets the min cluster size of the clusterer
	 *
	 * @param {number} minClusterSize The grid size of the clusterer.
	 */
	MarkerClusterer.prototype.setMinClusterSize = function(minClusterSize) {
		this.minClusterSize_ = minClusterSize;
	};

	/**
	 * Returns the min cluster size of the clusterer
	 *
	 * @return {number} The grid size of the clusterer.
	 */
	MarkerClusterer.prototype.getMinClusterSize = function() {
		return this.minClusterSize_;
	};

	/**
	 * Sets the max zoom level of the clusterer
	 *
	 * @param {number} maxZoom The max zoom level of the clusterer.
	 */
	MarkerClusterer.prototype.setMaxZoom = function(maxZoom) {
		this.maxZoom_ = maxZoom;
	};

	/**
	 * Returns the max zoom level of the clusterer
	 *
	 * @return {number} The max zoom level of the clusterer.
	 */
	MarkerClusterer.prototype.getMaxZoom = function() {
		return this.maxZoom_;
	};

	/**
	 * Sets the styles of the clusterer
	 *
	 * @param {Object} styles The styles of the clusterer.
	 */
	MarkerClusterer.prototype.setStyles = function(styles) {
		this.styles_ = styles;
	};

	/**
	 * Returns the styles of the clusterer
	 *
	 * @return {Object} The styles of the clusterer.
	 */
	MarkerClusterer.prototype.getStyles = function() {
		return this.styles_;
	};

	/**
	 * Returns the array of markers in the clusterer.
	 *
	 * @return {Array<naver.maps.Marker>} The markers in the clusterer.
	 */
	MarkerClusterer.prototype.getMarkers = function() {
		return this.markers_;
	};

	/**
	 * Returns the number of markers in the clusterer
	 *
	 * @return {number} The number of markers in the clusterer.
	 */
	MarkerClusterer.prototype.getTotalMarkers = function() {
		return this.markers_.length;
	};

	/**
	 * Returns the array of clusters in the clusterer.
	 *
	 * @return {Array<MarkerCluster>} The clusters in the clusterer.
	 */
	MarkerClusterer.prototype.getClusters = function() {
		return this.clusters_;
	};

	/**
	 * Returns the number of clusters in the clusterer.
	 *
	 * @return {number} The number of clusters in the clusterer.
	 */
	MarkerClusterer.prototype.getTotalClusters = function() {
		return this.clusters_.length;
	};

	/**
	 * Add a marker to the clusterer.
	 *
	 * @param {naver.maps.Marker} marker The marker to add.
	 * @param {boolean=} opt_nodraw Set to true to disable redraw after adding.
	 * @return {boolean} True if the marker was added.
	 */
	MarkerClusterer.prototype.addMarker = function(marker, opt_nodraw) {
		if (marker.isAddedToCluster_) {
			return false;
		}

		marker.isAddedToCluster_ = true;
		this.markers_.push(marker);

		if (!opt_nodraw) {
			this.redraw();
		}
		return true;
	};

	/**
	 * Add an array of markers to the clusterer.
	 *
	 * @param {Array<naver.maps.Marker>} markers The markers to add.
	 * @param {boolean=} opt_nodraw Set to true to disable redraw after adding.
	 */
	MarkerClusterer.prototype.addMarkers = function(markers, opt_nodraw) {
		for (var i = 0, marker; marker = markers[i]; i++) {
			this.addMarker(marker, true);
		}

		if (!opt_nodraw) {
			this.redraw();
		}
	};

	/**
	 * Remove a marker from the clusterer.
	 *
	 * @param {naver.maps.Marker} marker The marker to remove.
	 * @param {boolean=} opt_nodraw Set to true to disable redraw after removing.
	 * @return {boolean} True if the marker was removed.
	 */
	MarkerClusterer.prototype.removeMarker = function(marker, opt_nodraw) {
		var removed = this.removeMarker_(marker);

		if (!opt_nodraw && removed) {
			this.redraw();
		}
		return removed;
	};

	/**
	 * Removes a marker and returns true if it was removed, false otherwise.
	 * @param {naver.maps.Marker} marker The marker to remove
	 * @private
	 */
	MarkerClusterer.prototype.removeMarker_ = function(marker) {
		var index = -1;
		if (this.markers_.indexOf) {
			index = this.markers_.indexOf(marker);
		} else {
			for (var i = 0, m; m = this.markers_[i]; i++) {
				if (m == marker) {
					index = i;
					break;
				}
			}
		}

		if (index == -1) {
			return false;
		}

		marker.isAddedToCluster_ = false;
		this.markers_.splice(index, 1);

		return true;
	};

	/**
	 * Remove an array of markers from the clusterer.
	 *
	 * @param {Array<naver.maps.Marker>} markers The markers to remove.
	 * @param {boolean=} opt_nodraw Set to true to disable redraw after removing.
	 */
	MarkerClusterer.prototype.removeMarkers = function(markers, opt_nodraw) {
		var removed = false;

		for (var i = 0, marker; marker = markers[i]; i++) {
			removed = removed || this.removeMarker_(marker);
		}

		if (!opt_nodraw && removed) {
			this.redraw();
		}
	};

	/**
	 * Remove all markers from the clusterer.
	 */
	MarkerClusterer.prototype.clearMarkers = function() {
		this.resetViewport(true);
		this.markers_ = [];
	};

	/**
	 * Redraws the clusterer and all the clusters.
	 */
	MarkerClusterer.prototype.redraw = function() {
		this.resetViewport();
		this.createClusters();
	};

	/**
	 * Removes all clusters from the map and recreates them if `opt_hide` is set to true.
	 * @param {boolean=} opt_hide Set to true to hide the clusterer.
	 */
	MarkerClusterer.prototype.resetViewport = function(opt_hide) {
		for (var i = 0, cluster; cluster = this.clusters_[i]; i++) {
			cluster.remove();
		}
		this.clusters_ = [];

		for (var i = 0, marker; marker = this.markers_[i]; i++) {
			marker.isAddedToCluster_ = false;
			if (opt_hide) {
				marker.setMap(null);
			}
		}
	};

	/**
	 * Creates the clusters.
	 *
	 * @private
	 */
	MarkerClusterer.prototype.createClusters = function() {
		if (!this.ready_) {
			return;
		}

		var mapBounds = this.map_.getBounds();
		var zoom = this.map_.getZoom();
		var gridSize = this.gridSize_;
		var minClusterSize = this.minClusterSize_;
		var maxZoom = this.maxZoom_;

		// 최대 줌 레벨 이상이면 클러스터링을 하지 않고 모든 마커를 보여줌
		if (maxZoom !== null && zoom > maxZoom) {
			for (var i = 0, marker; marker = this.markers_[i]; i++) {
				marker.setMap(this.map_);
			}
			return;
		}

		for (var i = 0, marker; marker = this.markers_[i]; i++) {
			if (marker.isAddedToCluster_) {
				continue;
			}

			if (!mapBounds.hasLatLng(marker.getPosition())) {
				marker.setMap(null);
				continue;
			}
			
			var cluster = new MarkerCluster(this);
			cluster.addMarker(marker);
			this.assignMarkerToCluster_(cluster, marker);
		}
	};

	/**
	 * Assigns a marker to a cluster, or creates a new cluster if it doesn't fit in an existing one.
	 *
	 * @param {MarkerCluster} cluster The cluster to add the marker to.
	 * @param {naver.maps.Marker} marker The marker to add.
	 * @private
	 */
	MarkerClusterer.prototype.assignMarkerToCluster_ = function(cluster, marker) {
		var clusterAdded = false;
		for (var i = 0, c; c = this.clusters_[i]; i++) {
			if (c.isMarkerInClusterBounds(marker)) {
				c.addMarker(marker);
				clusterAdded = true;
				break;
			}
		}

		if (!clusterAdded) {
			this.clusters_.push(cluster);
		}
	};

	/**
	 * A cluster that contains markers.
	 *
	 * @param {MarkerClusterer} markerClusterer The MarkerClusterer managing the cluster.
	 * @constructor
	 * @ignore
	 */
	var MarkerCluster = function(markerClusterer) {
		this.markerClusterer_ = markerClusterer;
		this.map_ = markerClusterer.map_;
		this.gridSize_ = markerClusterer.gridSize_;
		this.minClusterSize_ = markerClusterer.minClusterSize_;
		this.styles_ = markerClusterer.styles_;
		this.clusterIcon_ = markerClusterer.clusterIcon_;
		this.disableClickZoom_ = markerClusterer.disableClickZoom_;
		this.markers_ = [];
		this.center_ = null;
		this.bounds_ = null;
		this.clusterIcon_ = new ClusterIcon(this, this.styles_);
	};

	/**
	 * Adds a marker to the cluster.
	 *
	 * @param {naver.maps.Marker} marker The marker to add.
	 */
	MarkerCluster.prototype.addMarker = function(marker) {
		marker.isAddedToCluster_ = true;
		this.markers_.push(marker);

		if (!this.center_) {
			this.center_ = marker.getPosition();
			this.calculateBounds_();
		} else {
			this.calculateBounds_();
		}

		if (this.markers_.length < this.minClusterSize_ && marker.getMap() != this.map_) {
			marker.setMap(this.map_);
		}

		if (this.markers_.length === this.minClusterSize_) {
			for (var i = 0, m; m = this.markers_[i]; i++) {
				m.setMap(null);
			}
		}

		if (this.markers_.length >= this.minClusterSize_ && this.markerClusterer_.map_.getZoom() <= this.markerClusterer_.maxZoom_) {
			this.clusterIcon_.setCenter(this.center_);
			this.clusterIcon_.setMap(this.map_);
		}

		this.updateIcon();
	};

	/**
	 * Calculates the bounds of the cluster.
	 *
	 * @private
	 */
	MarkerCluster.prototype.calculateBounds_ = function() {
		var bounds = new naver.maps.LatLngBounds(this.center_, this.center_);
		var latlng = this.center_;

		var neLat = latlng.lat() + this.gridSize_ / 2000; // 대략적인 위도 범위
		var neLng = latlng.lng() + this.gridSize_ / 2000; // 대략적인 경도 범위
		var swLat = latlng.lat() - this.gridSize_ / 2000;
		var swLng = latlng.lng() - this.gridSize_ / 2000;

		bounds.extend(new naver.maps.LatLng(neLat, neLng));
		bounds.extend(new naver.maps.LatLng(swLat, swLng));

		this.bounds_ = bounds;
	};

	/**
	 * Removes the cluster from the map.
	 */
	MarkerCluster.prototype.remove = function() {
		this.clusterIcon_.setMap(null);
		this.markers_ = [];
		delete this.markers_;
	};

	/**
	 * Returns the number of markers in the cluster.
	 *
	 * @return {number} The number of markers in the cluster.
	 */
	MarkerCluster.prototype.getSize = function() {
		return this.markers_.length;
	};

	/**
	 * Returns the array of markers in the cluster.
	 *
	 * @return {Array<naver.maps.Marker>} The markers in the cluster.
	 */
	MarkerCluster.prototype.getMarkers = function() {
		return this.markers_;
	};

	/**
	 * Returns the center of the cluster.
	 *
	 * @return {naver.maps.LatLng} The center of the cluster.
	 */
	MarkerCluster.prototype.getCenter = function() {
		return this.center_;
	};

	/**
	 * Returns the map in which the cluster is operating.
	 *
	 * @return {naver.maps.Map} The map in which the cluster is operating.
	 */
	MarkerCluster.prototype.getMap = function() {
		return this.map_;
	};

	/**
	 * Returns the bounds of the cluster.
	 *
	 * @return {naver.maps.LatLngBounds} The bounds of the cluster.
	 */
	MarkerCluster.prototype.getBounds = function() {
		var bounds = new naver.maps.LatLngBounds(this.center_, this.center_);
		for (var i = 0, marker; marker = this.markers_[i]; i++) {
			bounds.extend(marker.getPosition());
		}
		return bounds;
	};

	/**
	 * Tests to see if a marker is in the cluster bounds.
	 *
	 * @param {naver.maps.Marker} marker The marker to test.
	 * @return {boolean} True if the marker is in the cluster bounds.
	 */
	MarkerCluster.prototype.isMarkerInClusterBounds = function(marker) {
		return this.bounds_.hasLatLng(marker.getPosition());
	};

	/**
	 * Update the cluster icon.
	 */
	MarkerCluster.prototype.updateIcon = function() {
		var zoom = this.map_.getZoom();
		var maxZoom = this.markerClusterer_.maxZoom_;

		if (maxZoom !== null && zoom > maxZoom) {
			this.clusterIcon_.setMap(null);
			return;
		}

		if (this.markers_.length < this.minClusterSize_) {
			// 클러스터 최소 크기 미달 시 아이콘 숨김
			this.clusterIcon_.setMap(null);
			return;
		}

		this.clusterIcon_.setCount(this.markers_.length);
	};

	/**
	 * A cluster icon that contains the count of the markers in the cluster.
	 *
	 * @param {MarkerCluster} cluster The cluster to render.
	 * @param {Array<Object>} styles The array of styles to use.
	 * @constructor
	 * @extends naver.maps.OverlayView
	 * @ignore
	 */
	var ClusterIcon = function(cluster, styles) {
		this.cluster_ = cluster;
		this.styles_ = styles;
		this.center_ = null;
		this.map_ = cluster.getMap();
		this.div_ = null;
		this.sums_ = null;
		this.index_ = 0;
		this.timer_ = null;
		this.setupCss_();
	};

	// ClusterIcon extends Naver.maps.OverlayView
	ClusterIcon.prototype = new naver.maps.OverlayView();

	/**
	 * Sets up the css for the cluster icon.
	 *
	 * @private
	 */
	ClusterIcon.prototype.setupCss_ = function() {
		var element = this.container_ = document.createElement('div');
		element.style.cssText = 'position:absolute;cursor:pointer;text-align:center;';

		this.span_ = document.createElement('span');
		element.appendChild(this.span_);

		naver.maps.Event.addDOMListener(element, 'click', function(e) {
			var cluster = this.cluster_;
			var markerClusterer = cluster.markerClusterer_;
			var map = markerClusterer.map_;
			var markers = cluster.getMarkers();

			if (!cluster.disableClickZoom_) {
				// Zoom in to the cluster.
				var bounds = new naver.maps.LatLngBounds();
				for (var i = 0, marker; marker = markers[i]; i++) {
					bounds.extend(marker.getPosition());
				}
				map.fitBounds(bounds);
			}

			/**
			 * This event is fired when a cluster marker is clicked.
			 * @type {MouseEvent}
			 * @name MarkerClusterer#clusterclick
			 * @param {MarkerCluster} cluster The cluster that was clicked.
			 * @event
			 */
			naver.maps.Event.trigger(markerClusterer, 'clusterclick', cluster);
		}.bind(this)); // bind this context to the handler
	};

	/**
	 * Adds the icon to the map.
	 *
	 * @private
	 */
	ClusterIcon.prototype.onAdd = function() {
		this.div_ = this.container_;
		var panes = this.getPanes();
		panes.overlayMouseTarget.appendChild(this.div_);
	};

	/**
	 * Removes the icon from the map
	 *
	 * @private
	 */
	ClusterIcon.prototype.onRemove = function() {
		if (this.div_ && this.div_.parentNode) {
			this.div_.parentNode.removeChild(this.div_);
			this.div_ = null;
		}
	};

	/**
	 * Draws the icon.
	 *
	 * @private
	 */
	ClusterIcon.prototype.draw = function() {
		if (!this.getMap()) {
			return;
		}

		var projection = this.getProjection();
		var position = projection.fromLatLngToDivPixel(this.center_);
		var div = this.div_;

		div.style.left = position.x + 'px';
		div.style.top = position.y + 'px';

		this.updateIcon(); // 아이콘 업데이트 호출
	};

	/**
	 * Sets the center of the icon.
	 *
	 * @param {naver.maps.LatLng} center The center of the icon.
	 */
	ClusterIcon.prototype.setCenter = function(center) {
		this.center_ = center;
	};

	/**
	 * Sets the count of the markers in the cluster.
	 *
	 * @param {number} count The count of the markers in the cluster.
	 */
	ClusterIcon.prototype.setCount = function(count) {
		var bs = this.styles_;
		var style;
		for (var i = 0; i < bs.length; i++) {
			if (count >= bs[i].min) {
				style = bs[i];
			}
		}

		if (style) {
			this.container_.style.width = style.width + 'px';
			this.container_.style.height = style.height + 'px';
			this.container_.style.marginLeft = -style.width / 2 + 'px';
			this.container_.style.marginTop = -style.height / 2 + 'px';

			if (style.url) { // 이미지 URL이 있는 경우
				this.container_.style.backgroundImage = 'url(' + style.url + ')';
				this.container_.style.backgroundSize = 'contain';
				this.container_.style.backgroundRepeat = 'no-repeat';
				this.span_.style.display = 'none'; // 텍스트 숨김
			} else { // 이미지 URL이 없는 경우 (CSS 스타일 직접 적용)
				this.container_.style.background = style.background || 'rgba(0,0,0,0.6)';
				this.container_.style.borderRadius = style.borderRadius || '50%';
				this.container_.style.border = style.border || '2px solid white';
				this.container_.style.boxShadow = style.boxShadow || '0 0 5px rgba(0,0,0,0.5)';
				this.span_.style.display = 'block'; // 텍스트 표시
				this.span_.style.color = style.color || '#fff';
				this.span_.style.fontSize = style.fontSize || '14px';
				this.span_.style.lineHeight = style.lineHeight || style.height + 'px';
				this.span_.style.fontWeight = style.fontWeight || 'bold';
			}
			this.span_.innerHTML = count;
		} else {
			this.container_.style.display = 'none'; // 스타일이 없으면 숨김
		}

		this.container_.style.display = ''; // 다시 보이게
	};

	/**
	 * Sets the map on which the icon is to operate.
	 *
	 * @param {naver.maps.Map} map The map on which the icon is to operate.
	 */
	ClusterIcon.prototype.setMap = function(map) {
		this.map_ = map;
		if (map) {
			this.onAdd();
			this.draw();
		} else {
			this.onRemove();
		}
	};

	w.MarkerClusterer = MarkerClusterer;

})(window);
