/* ==========================================================================
   SKYROUTES DRONES · CLIENTE INTERACTIVO EN JAVASCRIPT NATIVO (ES6+)
   Comunica la vista minimalista con el servidor estándar http.server (/api/*)
   ========================================================================== */

(() => {
    "use strict";

    const uiState = {
        snapshot: null,
        selectedDroneId: "DR-02",
        selectedOrderId: "PED-4029",
        selectedCategory: "BUSQUEDA_RESCATE",
        inspectMode: "str",
        speedFactor: 1,
        autoSyncId: null,
        syncInFlight: false,
        routePreview: null,
        numericCache: {},
        orderSeq: 4030,
    };

    const $ = (id) => document.getElementById(id);

    // ======================================================================
    // COMUNICACIÓN CON EL PUENTE HTTP NATIVO (/api/*)
    // ======================================================================

    async function apiGet(path) {
        const resp = await fetch(path, { headers: { Accept: "application/json" } });
        const data = await resp.json();
        if (!resp.ok || data.ok === false) {
            throw data;
        }
        return data;
    }

    async function apiPost(path, payload = {}) {
        const resp = await fetch(path, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();
        if (!resp.ok || data.ok === false) {
            throw data;
        }
        return data;
    }

    // ======================================================================
    // ANIMACIÓN DE VALORES NUMÉRICOS
    // ======================================================================

    function animarNumero(elementId, valorObjetivo, decimales = 1) {
        const el = $(elementId);
        if (!el) return;

        const destino = Number(valorObjetivo) || 0;
        const inicio = uiState.numericCache[elementId] ?? destino;
        uiState.numericCache[elementId] = destino;

        if (Math.abs(destino - inicio) < 0.01) {
            el.textContent = destino.toFixed(decimales);
            return;
        }

        const duracionMs = 300;
        const t0 = performance.now();

        function frame(ahora) {
            const p = Math.min(1, (ahora - t0) / duracionMs);
            const ease = 1 - Math.pow(1 - p, 3);
            const actual = inicio + (destino - inicio) * ease;
            el.textContent = actual.toFixed(decimales);
            if (p < 1) {
                requestAnimationFrame(frame);
            }
        }
        requestAnimationFrame(frame);
    }

    // ======================================================================
    // MANEJO DEL BANNER DE EXCEPCIONES DE DOMINIO (RF-02)
    // ======================================================================

    function mostrarExcepcionDominio(err) {
        const banner = $("domainBanner");
        const nominal = $("bannerNominal");
        const errorBox = $("bannerError");

        const tipo = err?.error_tipo || "ExcepcionDominio";
        const mensaje = err?.mensaje || "Operación rechazada por validación de reglas de negocio.";
        const regla = err?.regla_negocio || "Validación de Dominio";

        $("errorTypeChip").textContent = tipo;
        $("errorDetailText").textContent = `— ${mensaje}`;
        $("errorRuleLabel").textContent = regla;

        nominal.classList.add("is-hidden");
        errorBox.classList.remove("is-hidden");
        banner.classList.remove("has-error");
        void banner.offsetWidth; // Reinicia animación CSS
        banner.classList.add("has-error");
    }

    function limpiarExcepcionDominio(mensajeNominal = null) {
        const banner = $("domainBanner");
        $("bannerError").classList.add("is-hidden");
        $("bannerNominal").classList.remove("is-hidden");
        banner.classList.remove("has-error");
        if (mensajeNominal) {
            $("operationToastText").textContent = mensajeNominal;
        }
    }

    // ======================================================================
    // OBTENCIÓN DE ENTIDADES SELECCIONADAS
    // ======================================================================

    function obtenerDronSeleccionado() {
        const flota = uiState.snapshot?.flota || [];
        return flota.find((d) => d.id_dron === uiState.selectedDroneId) || flota[0] || null;
    }

    function obtenerPedidoSeleccionado() {
        const pedidos = uiState.snapshot?.pedidos || [];
        return pedidos.find((p) => p.id_pedido === uiState.selectedOrderId) || pedidos[0] || null;
    }

    function formatearTupla(coords) {
        if (!Array.isArray(coords) || coords.length < 2) return "(6.2089, -75.5684)";
        return `(${Number(coords[0]).toFixed(4)}, ${Number(coords[1]).toFixed(4)})`;
    }

    // ======================================================================
    // RENDERIZADO DE LA VISTA COMPLETA
    // ======================================================================

    function renderizarTodo(datos) {
        uiState.snapshot = datos;

        if (datos.dron_enfocado_id) {
            uiState.selectedDroneId = datos.dron_enfocado_id;
        }
        if (datos.pedido_creado_id) {
            uiState.selectedOrderId = datos.pedido_creado_id;
        }
        if (datos.mensaje_operacion) {
            limpiarExcepcionDominio(datos.mensaje_operacion);
        }

        renderizarEncabezado(datos);
        renderizarTiraFlota(datos.flota || []);
        renderizarMonitoreoDron();
        renderizarCrucePedidos(datos.pedidos || []);
        renderizarNavegacionYRuta();
        renderizarRetornoBase();
        renderizarBitacora(datos.logs || []);
        renderizarModalUsuarios(datos.usuarios || [], datos.usuario_activo);
    }

    function renderizarEncabezado(datos) {
        const usr = datos.usuario_activo;
        if (usr) {
            $("activeUserName").textContent = usr.nombre;
            $("activeUserRole").textContent = `Rol: ${usr.rol}`;
        }
        $("lastSyncTime").textContent = (datos.ultima_sincronizacion || datos.timestamp || "").slice(0, 5);

        const clima = datos.clima;
        if (clima) {
            $("climateText").textContent = `${Number(clima.temperatura_c).toFixed(1)} °C · Viento ${Number(clima.viento_kmh).toFixed(1)} km/h`;
        }
    }

    function renderizarTiraFlota(flota) {
        const contenedor = $("fleetStrip");
        contenedor.innerHTML = "";

        const etiquetasCortas = {
            ENTREGA_LIGERA: "Entrega",
            CARGA_PESADA: "Carga",
            VIGILANCIA: "Vigilancia",
            MAPEO_TOPOGRAFICO: "Mapeo",
            INSPECCION_INFRAESTRUCTURA: "Inspección",
            BUSQUEDA_RESCATE: "Rescate",
        };

        flota.forEach((dron) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = `fleet-pill${dron.id_dron === uiState.selectedDroneId ? " is-selected" : ""}`;

            let dotClass = "dot-disponible";
            if (dron.estado_operacional === "EN_MISION") dotClass = "dot-vuelo";
            else if (dron.estado_operacional === "RETORNANDO_A_BASE") dotClass = "dot-retorno";
            else if (dron.estado_operacional === "RESERVADO") dotClass = "dot-reservado";

            btn.innerHTML = `
                <div class="fleet-pill-left">
                    <span class="fleet-pill-id">
                        <span class="status-dot ${dotClass}"></span>
                        ${dron.id_dron}
                    </span>
                    <span class="fleet-pill-cat">${etiquetasCortas[dron.categoria] || dron.categoria}</span>
                </div>
                <span class="fleet-pill-bat">${dron.bateria.toFixed(0)}%</span>
            `;

            btn.addEventListener("click", () => {
                uiState.selectedDroneId = dron.id_dron;
                if (dron.pedido_activo_id) {
                    uiState.selectedOrderId = dron.pedido_activo_id;
                }
                actualizarPreviewRutaSilencioso();
                renderizarTodo(uiState.snapshot);
            });

            contenedor.appendChild(btn);
        });
    }

    function renderizarMonitoreoDron() {
        const dron = obtenerDronSeleccionado();
        if (!dron) return;

        const catCorta = dron.categoria_etiqueta.toUpperCase();
        $("droneMonitorTitle").textContent = `${dron.id_dron} · ${catCorta}`;
        $("droneMonitorSubmeta").textContent = `${dron.modelo_aeronave} · Subclase ${dron.clase_python}`;

        animarNumero("telemetryBattery", dron.bateria, 1);
        animarNumero("telemetryAltitude", dron.altitud, 1);

        const batFill = $("batteryBarFill");
        batFill.style.width = `${Math.max(0, Math.min(100, dron.bateria))}%`;
        batFill.classList.toggle("is-low", dron.bateria < 20);
        batFill.classList.toggle("is-warn", dron.bateria >= 20 && dron.bateria < 45);

        const btnRecarga = $("btnRechargeDrone");
        const puedeRecargar = dron.disponible && !dron.en_mision && !dron.retornando_a_base && dron.bateria < 99.9;
        btnRecarga.classList.toggle("is-hidden", !puedeRecargar);

        $("telemetryMotors").textContent = `'${dron.estado_motores}'`;
        $("telemetryCoords").textContent = formatearTupla(dron.coordenadas);
        $("telemetryOdometer").textContent = `${dron.kilometraje_total_km.toFixed(2)} km · ${dron.consumo_10km_pct.toFixed(1)}% / 10 km`;

        // Atributos propios de la subclase
        const specsGrid = $("subclassSpecsGrid");
        specsGrid.innerHTML = (dron.especificaciones || [])
            .map(
                (sp) => `
                <div class="spec-mini-box">
                    <small>${sp.etiqueta}</small>
                    <strong>${sp.valor}</strong>
                </div>
            `
            )
            .join("");

        // Inspección técnica (__str__, __repr__, inspeccionar_sistemas_especializados)
        const salida = $("entityInspectionOutput");
        const pie = $("inspectionFooterNote");
        if (uiState.inspectMode === "repr") {
            salida.textContent = dron.ficha_repr;
            pie.textContent = `Método dunder __repr__ heredado y sobrescrito en ${dron.clase_python}`;
        } else if (uiState.inspectMode === "sistemas") {
            salida.textContent = dron.diagnostico_sistemas;
            pie.textContent = `Método abstracto @abstractmethod inspeccionar_sistemas_especializados()`;
        } else {
            salida.textContent = dron.ficha_str;
            pie.textContent = `Método dunder __str__ polimórfico en ${dron.clase_python}`;
        }
    }

    function renderizarCrucePedidos(pedidos) {
        const selector = $("selectActiveOrder");
        if (pedidos.length === 0) {
            selector.innerHTML = `<option value="">Sin pedidos registrados</option>`;
            return;
        }

        if (!pedidos.some((p) => p.id_pedido === uiState.selectedOrderId)) {
            uiState.selectedOrderId = pedidos[0].id_pedido;
        }

        selector.innerHTML = pedidos
            .map(
                (p) =>
                    `<option value="${p.id_pedido}" ${p.id_pedido === uiState.selectedOrderId ? "selected" : ""}>
                        #${p.id_pedido} · ${p.categoria_etiqueta} (${p.estado})
                    </option>`
            )
            .join("");

        const pedido = obtenerPedidoSeleccionado();
        if (!pedido) return;

        $("selectedOrderStateBadge").textContent = pedido.estado;
        $("assignOrderId").textContent = `#${pedido.id_pedido} (${pedido.peso_carga_kg.toFixed(1)} kg)`;
        $("assignCategory").textContent = pedido.categoria_etiqueta;

        const droneBadge = $("assignDroneBadge");
        if (pedido.dron_asignado_id) {
            droneBadge.textContent = `${pedido.dron_asignado_id} (Vinculado)`;
        } else if (pedido.dron_sugerido_id) {
            droneBadge.textContent = `${pedido.dron_sugerido_id} (Disponible)`;
        } else {
            droneBadge.textContent = "Sin dron disponible";
        }

        const viabText = $("assignViabilityText");
        if (pedido.viabilidad) {
            const v = pedido.viabilidad;
            const estadoViab = v.es_viable ? "Viable" : "Riesgo / Exceso";
            viabText.textContent = `${v.consumo_estimado_pct}% req. (${v.distancia_km} km) · ${estadoViab}`;
        } else {
            viabText.textContent = `${pedido.distancia_desde_base_km} km desde base`;
        }

        const btnAssign = $("btnAssignOrder");
        const dispatchWrap = $("dispatchButtonsWrap");

        if (pedido.estado === "PENDIENTE") {
            btnAssign.classList.remove("is-hidden");
            btnAssign.disabled = false;
            btnAssign.textContent = "Confirmar Asignación de Dron";
            dispatchWrap.classList.add("is-hidden");
        } else if (pedido.estado === "ASIGNADO") {
            btnAssign.classList.add("is-hidden");
            dispatchWrap.classList.remove("is-hidden");
        } else {
            btnAssign.classList.remove("is-hidden");
            btnAssign.disabled = true;
            btnAssign.textContent = `Estado del Pedido: ${pedido.estado}`;
            dispatchWrap.classList.add("is-hidden");
        }
    }

    function renderizarNavegacionYRuta() {
        const dron = obtenerDronSeleccionado();
        const base = uiState.snapshot?.coordenadas_base || [6.2089, -75.5684];
        if (!dron) return;

        $("routeOriginCoords").textContent = formatearTupla(base);
        $("navCruiseSpeed").textContent = `Vel. crucero: ${dron.velocidad_promedio_kmh.toFixed(0)} km/h`;

        const track = document.querySelector(".route-vector-track");
        const marker = $("routePlaneMarker");

        if (dron.estado_operacional === "EN_MISION") {
            $("routeDestTitle").textContent = dron.pedido_activo_id ? `Destino ${dron.pedido_activo_id}` : "Destino";
            $("routeDestCoords").textContent = formatearTupla(dron.destino_actual);
            animarNumero("navDistanceKm", dron.distancia_objetivo_km, 2);
            animarNumero("navEtaMin", dron.eta_min, 1);

            track.classList.add("is-flying");
            marker.classList.remove("is-returning");
            marker.style.left = `${Math.max(4, Math.min(96, dron.progreso_mision_pct))}%`;
        } else if (dron.estado_operacional === "RETORNANDO_A_BASE") {
            $("routeDestTitle").textContent = "Retorno a Base";
            $("routeDestCoords").textContent = formatearTupla(dron.coordenadas);
            animarNumero("navDistanceKm", dron.distancia_a_base_km, 2);
            animarNumero("navEtaMin", dron.eta_min, 1);

            track.classList.add("is-flying");
            marker.classList.add("is-returning");
            const posRetorno = 100 - dron.progreso_retorno_pct;
            marker.style.left = `${Math.max(4, Math.min(96, posRetorno))}%`;
        } else {
            track.classList.remove("is-flying");
            marker.classList.remove("is-returning");
            marker.style.left = "5%";

            const preview = uiState.routePreview;
            if (preview && preview.id_dron === dron.id_dron) {
                $("routeDestTitle").textContent = "Destino Proyectado";
                $("routeDestCoords").textContent = formatearTupla(preview.destino);
                animarNumero("navDistanceKm", preview.distancia_km, 2);
                animarNumero("navEtaMin", preview.eta_min, 1);
            } else {
                const latInput = parseFloat($("inputDestLat").value) || 6.2620;
                const lonInput = parseFloat($("inputDestLon").value) || -75.5780;
                $("routeDestTitle").textContent = "Destino Solicitud";
                $("routeDestCoords").textContent = formatearTupla([latInput, lonInput]);
                animarNumero("navDistanceKm", dron.distancia_objetivo_km || 5.99, 2);
                animarNumero("navEtaMin", dron.eta_min || 5.5, 1);
            }
        }
    }

    function renderizarRetornoBase() {
        const dron = obtenerDronSeleccionado();
        if (!dron) return;

        const bloqueado = !dron.disponible || dron.en_mision || dron.retornando_a_base;
        const lockTitle = $("returnLockTitle");
        const flagBadge = $("returnFlagBadge");
        const bar = $("returnProgressBar");
        const distLabel = $("returnDistanceLabel");
        const pctLabel = $("returnPctLabel");
        const btnTrigger = $("btnTriggerReturn");
        const btnFinalize = $("btnFinalizeReturn");
        const lockIcon = $("returnLockIcon");

        flagBadge.textContent = `retornando_a_base = ${dron.retornando_a_base ? "True" : "False"}`;

        if (bloqueado) {
            lockTitle.textContent = "Disponibilidad Bloqueada";
            lockIcon.innerHTML = `
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            `;
        } else {
            lockTitle.textContent = "Disponible en Sede Base";
            lockIcon.innerHTML = `
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
            `;
        }

        if (dron.retornando_a_base) {
            bar.style.width = `${dron.progreso_retorno_pct}%`;
            distLabel.textContent = `Distancia restante a base: ${dron.distancia_a_base_km.toFixed(2)} km`;
            pctLabel.textContent = `${dron.progreso_retorno_pct.toFixed(0)}% completado`;
            btnTrigger.classList.add("is-hidden");
            btnFinalize.disabled = false;
        } else if (dron.en_mision) {
            bar.style.width = "0%";
            distLabel.textContent = `Aeronave en misión activa (${dron.distancia_a_base_km.toFixed(2)} km de base)`;
            pctLabel.textContent = "En tránsito";
            btnTrigger.classList.remove("is-hidden");
            btnFinalize.disabled = false;
        } else {
            bar.style.width = "100%";
            distLabel.textContent = `Estacionado en Base Medellín (${dron.distancia_a_base_km.toFixed(2)} km)`;
            pctLabel.textContent = "En tierra";
            btnTrigger.classList.add("is-hidden");
            btnFinalize.disabled = false;
        }
    }

    function renderizarBitacora(logs) {
        $("auditCountBadge").textContent = `${logs.length} eventos recientes`;
        const tbody = $("auditTableBody");
        tbody.innerHTML = logs
            .map(
                (log) => `
                <tr>
                    <td>${(log.fecha_hora || "").split(" ")[1] || log.fecha_hora}</td>
                    <td><strong>${log.tipo_evento}</strong></td>
                    <td>${log.id_dron}</td>
                    <td>${log.id_pedido}</td>
                    <td>${log.detalles}</td>
                </tr>
            `
            )
            .join("");
    }

    function renderizarModalUsuarios(usuarios, activo) {
        const lista = $("userSwitchList");
        lista.innerHTML = "";

        usuarios.forEach((u) => {
            const btn = document.createElement("button");
            btn.type = "button";
            const esActual = activo && u.id_usuario === activo.id_usuario;
            btn.className = `user-option-btn${esActual ? " is-current" : ""}`;
            btn.innerHTML = `
                <span><strong>${u.nombre}</strong> <small class="mono-muted">(${u.id_usuario})</small></span>
                <span class="rf-tag">${u.rol}</span>
            `;
            btn.addEventListener("click", async () => {
                try {
                    const res = await apiPost("/api/usuarios", { accion: "cambiar", id_usuario: u.id_usuario });
                    $("userModalBackdrop").classList.add("is-hidden");
                    renderizarTodo(res);
                } catch (err) {
                    mostrarExcepcionDominio(err);
                }
            });
            lista.appendChild(btn);
        });
    }

    // ======================================================================
    // CÁLCULO DE PREVIEW GEODÉSICO EN VIVO
    // ======================================================================

    async function actualizarPreviewRutaSilencioso() {
        const lat = parseFloat($("inputDestLat").value);
        const lon = parseFloat($("inputDestLon").value);
        if (Number.isNaN(lat) || Number.isNaN(lon)) return;

        try {
            const prev = await apiGet(
                `/api/ruta-preview?id_dron=${encodeURIComponent(uiState.selectedDroneId)}&lat=${lat}&lon=${lon}`
            );
            uiState.routePreview = prev;
            renderizarNavegacionYRuta();
        } catch (_) {
            // Si las coordenadas editadas salen del polígono mientras se escribe, se valida al enviar
        }
    }

    // ======================================================================
    // INICIALIZACIÓN DE EVENTOS E INTERACCIONES
    // ======================================================================

    function poblarDestinosReferencia(destinos) {
        const sel = $("selectDestinationPreset");
        sel.innerHTML = "";

        destinos.forEach((d, idx) => {
            const opt = document.createElement("option");
            opt.value = String(idx);
            opt.textContent = `(${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}) · ${d.nombre}`;
            sel.appendChild(opt);
        });

        const optCustom = document.createElement("option");
        optCustom.value = "custom_coords";
        optCustom.textContent = "Coordenadas personalizadas (Lat, Lon)";
        sel.appendChild(optCustom);

        const optGeo = document.createElement("option");
        optGeo.value = "geocoder_osm";
        optGeo.textContent = "Geocodificar dirección textual (OSM / Catálogo Aburrá)";
        sel.appendChild(optGeo);

        sel.addEventListener("change", () => {
            const val = sel.value;
            const coordsRow = $("customDestinationFields");
            const addrRow = $("addressGeocoderField");

            if (val === "geocoder_osm") {
                coordsRow.classList.add("is-hidden");
                addrRow.classList.remove("is-hidden");
            } else {
                coordsRow.classList.remove("is-hidden");
                addrRow.classList.add("is-hidden");
                if (val !== "custom_coords") {
                    const item = destinos[Number(val)];
                    if (item) {
                        $("inputDestLat").value = item.lat.toFixed(4);
                        $("inputDestLon").value = item.lon.toFixed(4);
                        actualizarPreviewRutaSilencioso();
                    }
                }
            }
        });
    }

    async function ejecutarSincronizacion(manual = false) {
        if (uiState.syncInFlight) return;
        uiState.syncInFlight = true;

        const icon = $("syncIcon");
        if (manual) {
            icon.classList.remove("is-spinning");
            void icon.offsetWidth;
            icon.classList.add("is-spinning");
        }

        try {
            const payload = {
                factor_tiempo: uiState.speedFactor,
                consultar_clima: manual,
            };
            if (manual && uiState.speedFactor > 1) {
                payload.paso_fijo_seg = uiState.speedFactor * 2.0;
            }
            const res = await apiPost("/api/sincronizar", payload);
            renderizarTodo(res);
        } catch (err) {
            mostrarExcepcionDominio(err);
        } finally {
            uiState.syncInFlight = false;
        }
    }

    function vincularEventosDOM() {
        // Sincronización manual RF-05
        $("btnSyncFleet").addEventListener("click", () => ejecutarSincronizacion(true));

        // Selector de multiplicador Delta-t
        document.querySelectorAll(".speed-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".speed-btn").forEach((b) => b.classList.remove("is-active"));
                btn.classList.add("is-active");
                uiState.speedFactor = Number(btn.dataset.speed) || 1;
            });
        });

        // Auto-Sync periódico no bloqueante
        $("btnAutoSync").addEventListener("click", () => {
            const btn = $("btnAutoSync");
            if (uiState.autoSyncId) {
                clearInterval(uiState.autoSyncId);
                uiState.autoSyncId = null;
                btn.classList.remove("is-running");
                btn.setAttribute("aria-pressed", "false");
            } else {
                // Asegurar velocidad fluida por defecto al activar modo automático
                if (uiState.speedFactor === 1) {
                    uiState.speedFactor = 20;
                    document.querySelectorAll(".speed-btn").forEach((b) => {
                        b.classList.toggle("is-active", b.dataset.speed === "20");
                    });
                }
                uiState.autoSyncId = setInterval(() => ejecutarSincronizacion(false), 950);
                btn.classList.add("is-running");
                btn.setAttribute("aria-pressed", "true");
            }
        });

        // Cerrar y probar alerta de excepción RF-02
        $("btnDismissError").addEventListener("click", () => limpiarExcepcionDominio());
        $("btnQuickTestError").addEventListener("click", async () => {
            try {
                await apiPost("/api/telemetria", {
                    id_dron: uiState.selectedDroneId,
                    bateria: -5.0,
                });
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Pestañas de inspección (__str__, __repr__, sistemas)
        document.querySelectorAll(".seg-tab").forEach((tab) => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".seg-tab").forEach((t) => t.classList.remove("is-active"));
                tab.classList.add("is-active");
                uiState.inspectMode = tab.dataset.inspect;
                renderizarMonitoreoDron();
            });
        });

        // Selección de las 6 categorías de drones
        document.querySelectorAll(".cat-card").forEach((card) => {
            card.addEventListener("click", () => {
                document.querySelectorAll(".cat-card").forEach((c) => c.classList.remove("is-selected"));
                card.classList.add("is-selected");
                uiState.selectedCategory = card.dataset.category;

                // Enfocar automáticamente una aeronave de esa categoría si existe
                const dronCat = (uiState.snapshot?.flota || []).find((d) => d.categoria === uiState.selectedCategory);
                if (dronCat) {
                    uiState.selectedDroneId = dronCat.id_dron;
                    actualizarPreviewRutaSilencioso();
                    renderizarTodo(uiState.snapshot);
                }
            });
        });

        // Generador de ID de pedido
        $("btnGenOrderId").addEventListener("click", () => {
            uiState.orderSeq += 1;
            $("inputOrderId").value = `PED-${uiState.orderSeq}`;
        });

        // Cambio en coordenadas actualiza preview geodésico
        ["inputDestLat", "inputDestLon"].forEach((id) => {
            $(id).addEventListener("input", () => actualizarPreviewRutaSilencioso());
        });

        // Registrar nueva solicitud de pedido (RF-07)
        $("formNewOrder").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const modoDestino = $("selectDestinationPreset").value;
            const payload = {
                id_pedido: $("inputOrderId").value.trim(),
                categoria_requerida: uiState.selectedCategory,
                peso_carga_kg: parseFloat($("inputOrderWeight").value || "0"),
            };

            if (modoDestino === "geocoder_osm") {
                payload.direccion_destino = $("inputDestAddress").value.trim();
            } else {
                payload.latitud = parseFloat($("inputDestLat").value);
                payload.longitud = parseFloat($("inputDestLon").value);
                const optText = $("selectDestinationPreset").selectedOptions[0]?.textContent || "";
                if (optText.includes("·")) {
                    payload.direccion_destino = optText.split("·")[1].trim();
                }
            }

            try {
                const res = await apiPost("/api/pedidos", payload);
                uiState.orderSeq += 1;
                $("inputOrderId").value = `PED-${uiState.orderSeq}`;
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Selector de pedido activo
        $("selectActiveOrder").addEventListener("change", (ev) => {
            uiState.selectedOrderId = ev.target.value;
            const ped = obtenerPedidoSeleccionado();
            if (ped?.dron_asignado_id) {
                uiState.selectedDroneId = ped.dron_asignado_id;
            }
            renderizarTodo(uiState.snapshot);
        });

        // Cruzar y asignar dron (RF-08)
        $("btnAssignOrder").addEventListener("click", async () => {
            const ped = obtenerPedidoSeleccionado();
            if (!ped) return;
            try {
                const res = await apiPost("/api/pedidos/asignar", { id_pedido: ped.id_pedido });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Despachar misión simulada Delta-t vs instantánea (HU-12)
        $("btnDispatchSimulated").addEventListener("click", async () => {
            const ped = obtenerPedidoSeleccionado();
            if (!ped) return;
            try {
                const res = await apiPost("/api/pedidos/despachar", {
                    id_pedido: ped.id_pedido,
                    modo: "SIMULADO",
                });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        $("btnDispatchInstant").addEventListener("click", async () => {
            const ped = obtenerPedidoSeleccionado();
            if (!ped) return;
            try {
                const res = await apiPost("/api/pedidos/despachar", {
                    id_pedido: ped.id_pedido,
                    modo: "INSTANTANEO",
                });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Retorno obligatorio a base y aterrizaje (RF-09)
        $("btnTriggerReturn").addEventListener("click", async () => {
            try {
                const res = await apiPost("/api/drones/retorno", { id_dron: uiState.selectedDroneId });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        $("btnFinalizeReturn").addEventListener("click", async () => {
            try {
                const res = await apiPost("/api/drones/aterrizar", { id_dron: uiState.selectedDroneId });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Recarga de batería en plataforma
        $("btnRechargeDrone").addEventListener("click", async () => {
            try {
                const res = await apiPost("/api/drones/recargar", { id_dron: uiState.selectedDroneId });
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Acordeón de inyección de telemetría (RF-01 / RF-02)
        $("btnToggleInjector").addEventListener("click", () => {
            const btn = $("btnToggleInjector");
            const body = $("formTelemetryInjector");
            const expandido = btn.getAttribute("aria-expanded") === "true";
            btn.setAttribute("aria-expanded", String(!expandido));
            body.classList.toggle("is-collapsed", expandido);
        });

        document.querySelectorAll(".chip-test-btn").forEach((chip) => {
            chip.addEventListener("click", async () => {
                const tipo = chip.dataset.test;
                let payload = { id_dron: uiState.selectedDroneId };
                if (tipo === "bateria") {
                    payload.bateria = -5.0;
                } else if (tipo === "altitud") {
                    payload.altitud = 145.0;
                    payload.estado_motores = "EN_VUELO";
                } else if (tipo === "coherencia") {
                    payload.altitud = 0.0;
                    payload.estado_motores = "EN_VUELO";
                }
                try {
                    const res = await apiPost("/api/telemetria", payload);
                    renderizarTodo(res);
                } catch (err) {
                    mostrarExcepcionDominio(err);
                }
            });
        });

        $("formTelemetryInjector").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const payload = {
                id_dron: uiState.selectedDroneId,
                bateria: $("injBattery").value,
                altitud: $("injAltitude").value,
                estado_motores: $("injMotors").value,
            };
            try {
                const res = await apiPost("/api/telemetria", payload);
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });

        // Bitácora colapsable
        $("btnToggleAudit").addEventListener("click", () => {
            const btn = $("btnToggleAudit");
            const panel = $("auditPanelBody");
            const exp = btn.getAttribute("aria-expanded") === "true";
            btn.setAttribute("aria-expanded", String(!exp));
            panel.classList.toggle("is-collapsed", exp);
        });

        // Modal de Usuarios (RF-06)
        $("btnOpenUserModal").addEventListener("click", () => {
            $("userModalBackdrop").classList.remove("is-hidden");
        });
        $("btnCloseUserModal").addEventListener("click", () => {
            $("userModalBackdrop").classList.add("is-hidden");
        });
        $("userModalBackdrop").addEventListener("click", (ev) => {
            if (ev.target === $("userModalBackdrop")) {
                $("userModalBackdrop").classList.add("is-hidden");
            }
        });

        $("formRegisterUser").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            try {
                const res = await apiPost("/api/usuarios", {
                    accion: "registrar",
                    id_usuario: $("newUserId").value.trim(),
                    nombre: $("newUserName").value.trim(),
                    rol: $("newUserRole").value,
                });
                $("newUserId").value = "";
                $("newUserName").value = "";
                $("userModalBackdrop").classList.add("is-hidden");
                renderizarTodo(res);
            } catch (err) {
                mostrarExcepcionDominio(err);
            }
        });
    }

    // ======================================================================
    // ARRANQUE INICIAL DE LA CONSOLA
    // ======================================================================

    async function inicializarAplicacion() {
        vincularEventosDOM();
        try {
            const datos = await apiGet("/api/estado");
            poblarDestinosReferencia(datos.destinos_referencia || []);
            renderizarTodo(datos);
            await actualizarPreviewRutaSilencioso();
        } catch (err) {
            mostrarExcepcionDominio(err);
        }
    }

    document.addEventListener("DOMContentLoaded", inicializarAplicacion);
})();
