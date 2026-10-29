/* ==========================================================================
   SKYROUTE DRONES · LÓGICA DE INTERFAZ Y PUENTE CON HTTP.SERVER NATIVO (v3)
   100% acoplada a las entidades reales de Develop · Cero datos hardcodeados
   ========================================================================== */

(() => {
    "use strict";

    const estadoUI = {
        snapshot: null,
        vistaActiva: "operaciones",
        dronCabinaId: "DRON-ENT-01",
        dronInspectorId: "DRON-ENT-01",
        modoSimulacion: "paso", // "paso" | "auto" | "realtime"
        simularSoloEnfocado: false, // false: simula toda la flota activa simultáneamente
        timerAuto: null,
        timerRealtime: null,
        cadenciaRealtimeSeg: 5,
        modoDestinoPedido: "direccion", // "direccion" | "coordenadas"
        filtroPedidos: "TODOS",
        distanciaPolimorfismoKm: 15.0,
        datosPolimorfismo: null,
        selectsInicializados: false,
        tema: localStorage.getItem("skyroute_theme") || "light",
    };

    const $ = (id) => document.getElementById(id);

    function aplicarTema(tema) {
        const temaValido = tema === "dark" ? "dark" : "light";
        estadoUI.tema = temaValido;
        document.documentElement.setAttribute("data-theme", temaValido);
        try {
            localStorage.setItem("skyroute_theme", temaValido);
        } catch (_e) {}

        const iconDark = $("iconThemeDark");
        const iconLight = $("iconThemeLight");
        const label = $("labelToggleTheme");
        if (iconDark && iconLight) {
            iconDark.classList.toggle("is-hidden", temaValido === "dark");
            iconLight.classList.toggle("is-hidden", temaValido !== "dark");
        }
        if (label) {
            label.textContent = temaValido === "dark" ? "Modo Claro" : "Consola Oscura";
        }
    }

    function escaparHtml(valor) {
        return String(valor ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function clasePildoraEstado(estado) {
        const clave = String(estado || "").toUpperCase();
        if (["DISPONIBLE", "COMPLETADO", "LLEGADA_A_BASE", "MISION_COMPLETADA"].includes(clave)) {
            return "pill-ok";
        }
        if (["EN_MISION", "EN_TRANSITO", "EN_VUELO", "HACIA_DESTINO", "LLEGADA_A_DESTINO", "DESPEGUE_EXITOSO"].includes(clave)) {
            return "pill-active";
        }
        if (["ASIGNADO", "RESERVADO", "RETORNANDO_A_BASE", "PENDIENTE"].includes(clave)) {
            return "pill-warn";
        }
        if (["SIN_BATERIA", "BATERIA_AGOTADA", "CANCELADO", "EMERGENCIA_BATERIA"].includes(clave)) {
            return "pill-danger";
        }
        return "";
    }

    function barraBateriaMiniHtml(porcentaje) {
        const pct = Math.max(0, Math.min(100, Number(porcentaje) || 0));
        const mod = pct <= 20 ? "bat-low" : pct <= 50 ? "bat-mid" : "";
        return `
            <span class="mini-bat">
                <span class="mini-bat-track">
                    <span class="mini-bat-fill ${mod}" style="width: ${pct.toFixed(1)}%;"></span>
                </span>
                <span class="tabular-nums">${pct.toFixed(1)}%</span>
            </span>
        `;
    }

    // ==========================================================================
    // COMUNICACIÓN HTTP Y NOTIFICACIONES DE DOMINIO
    // ==========================================================================

    function mostrarNotificacion({ tipo = "info", insignia = "SISTEMA", titulo = "", mensaje = "" }) {
        const banner = $("feedbackBanner");
        banner.classList.remove("is-hidden", "is-error", "is-success");
        if (tipo === "error") banner.classList.add("is-error");
        if (tipo === "success") banner.classList.add("is-success");

        $("feedbackBadge").textContent = insignia;
        $("feedbackTitle").textContent = titulo;
        $("feedbackMessage").textContent = mensaje;
    }

    async function peticionAPI(ruta, opciones = {}) {
        const config = {
            method: opciones.metodo || "GET",
            headers: { "Content-Type": "application/json" },
        };
        if (opciones.cuerpo !== undefined) {
            config.body = JSON.stringify(opciones.cuerpo);
        }

        const resp = await fetch(ruta, config);
        const payload = await resp.json();

        if (!resp.ok || payload.ok === false) {
            mostrarNotificacion({
                tipo: "error",
                insignia: payload.regla_negocio || payload.error_tipo || "EXCEPCIÓN DE DOMINIO",
                titulo: payload.error_tipo || "Operación rechazada por validación",
                mensaje: payload.mensaje || "No fue posible procesar la solicitud.",
            });
            const err = new Error(payload.mensaje || "Error en petición HTTP");
            err.payload = payload;
            throw err;
        }
        return payload;
    }

    function aplicarSnapshot(snapshot, mostrarMensaje = true) {
        estadoUI.snapshot = snapshot;

        // Desacoplamiento de foco: se respeta la selección explícita del operador
        if (!estadoUI.dronCabinaId) {
            estadoUI.dronCabinaId = snapshot.dron_enfocado_id || (snapshot.flota[0] && snapshot.flota[0].id_dron);
            estadoUI.dronInspectorId = estadoUI.dronCabinaId;
        } else if (snapshot.dron_enfocado_id && snapshot.dron_enfocado_id !== estadoUI.dronCabinaId) {
            // Solo sincronizar automáticamente ante acciones manuales explícitas con mensaje (despegue, recarga)
            // y NUNCA durante pulsos de simulación periódica (evita secuestro de pantalla)
            if (snapshot.mensaje_operacion && !snapshot.pulsos_emitidos && !snapshot.delta_aplicado_seg) {
                estadoUI.dronCabinaId = snapshot.dron_enfocado_id;
                estadoUI.dronInspectorId = snapshot.dron_enfocado_id;
            }
        }

        // Si el dron seleccionado fue eliminado o no existe, restaurar el primero de la flota
        const dronExiste = snapshot.flota && snapshot.flota.some((d) => d.id_dron === estadoUI.dronCabinaId);
        if (!dronExiste && snapshot.flota && snapshot.flota.length > 0) {
            estadoUI.dronCabinaId = snapshot.flota[0].id_dron;
        }

        if (!estadoUI.selectsInicializados) {
            inicializarSelectoresEstaticos(snapshot);
            estadoUI.selectsInicializados = true;
        }

        renderizarBarraGlobal(snapshot);
        renderizarCabinaOperaciones(snapshot);
        renderizarFlotaEInspector(snapshot);
        renderizarDespachoYUsuarios(snapshot);
        renderizarBitacora(snapshot);

        if (estadoUI.vistaActiva === "polimorfismo") {
            cargarComparativaPolimorfica(estadoUI.distanciaPolimorfismoKm, false);
        }

        if (mostrarMensaje && snapshot.mensaje_operacion) {
            mostrarNotificacion({
                tipo: "success",
                insignia: "OPERACIÓN CONFIRMADA",
                titulo: "Estado actualizado en el Centro de Control",
                mensaje: snapshot.mensaje_operacion,
            });
        }
    }

    // ==========================================================================
    // NAVEGACIÓN ENTRE ESPACIOS DE TRABAJO
    // ==========================================================================

    function cambiarVista(nombreVista) {
        estadoUI.vistaActiva = nombreVista;
        document.querySelectorAll(".workspace-tab").forEach((btn) => {
            btn.classList.toggle("is-active", btn.dataset.view === nombreVista);
        });
        document.querySelectorAll(".workspace-view").forEach((sec) => {
            sec.classList.toggle("is-active", sec.id === `view-${nombreVista}`);
        });

        if (nombreVista === "polimorfismo") {
            cargarComparativaPolimorfica(estadoUI.distanciaPolimorfismoKm, false);
        }
    }

    // ==========================================================================
    // INICIALIZACIÓN DE SELECTORES Y BARRA SUPERIOR GLOBAL
    // ==========================================================================

    function inicializarSelectoresEstaticos(snapshot) {
        // Nodos climáticos del Valle de Aburrá
        const selClima = $("selectNodoClima");
        selClima.innerHTML = snapshot.nodos_clima
            .map((nodo) => `<option value="${escaparHtml(nodo)}">${escaparHtml(nodo.replace(/_/g, " "))}</option>`)
            .join("");
        selClima.value = snapshot.clima.nodo || "El_Poblado";

        // Categorías de pedidos
        const selCatPedido = $("pedCategoria");
        selCatPedido.innerHTML = snapshot.categorias_permitidas
            .map(
                (cat) =>
                    `<option value="${escaparHtml(cat)}">${escaparHtml(snapshot.etiquetas_categoria[cat] || cat)} (${escaparHtml(cat)})</option>`
            )
            .join("");

        // Categorías de fábrica de drones
        const selCatFabrica = $("fabCategoria");
        selCatFabrica.innerHTML = snapshot.categorias_fabrica
            .map(
                (cat) =>
                    `<option value="${escaparHtml(cat)}">${escaparHtml(snapshot.etiquetas_categoria[cat] || cat)} (${escaparHtml(cat)})</option>`
            )
            .join("");
        renderizarCamposDinamicosFabrica(selCatFabrica.value);

        // Chips de sugerencias viales rápidas
        const contSug = $("addressSuggestions");
        contSug.innerHTML = snapshot.sugerencias_direcciones
            .map(
                (item) =>
                    `<button type="button" class="chip-btn" data-dir-sugerida="${escaparHtml(item.direccion)}">${escaparHtml(item.etiqueta)}</button>`
            )
            .join("");
    }

    function renderizarBarraGlobal(snapshot) {
        const [latB, lonB] = snapshot.coordenadas_base;
        $("baseCoordsBadge").textContent = `Base Olaya Herrera · ${latB.toFixed(4)}, ${lonB.toFixed(4)}`;

        // Clima
        const clima = snapshot.clima;
        if ($("selectNodoClima").value !== clima.nodo) {
            $("selectNodoClima").value = clima.nodo;
        }
        $("climateReadout").textContent =
            `${Number(clima.temperatura_c).toFixed(1)} C · ${Number(clima.viento_kmh).toFixed(1)} km/h · ${(Number(clima.factor_velocidad) * 100).toFixed(0)}%`;
        const dotClima = $("climateSafetyDot");
        dotClima.className = `status-dot ${clima.vuelo_seguro ? "status-online" : "status-alert"}`;
        dotClima.title = clima.vuelo_seguro
            ? "Condiciones atmosféricas seguras para despegue"
            : "Alerta meteorológica activa";

        // Usuario activo
        $("topActiveUserName").textContent = snapshot.usuario_activo.nombre;
        $("topActiveUserRole").textContent = `${snapshot.usuario_activo.rol} · ${snapshot.usuario_activo.id_usuario}`;

        // Contadores de pestañas y KPIs
        const m = snapshot.metricas;
        const misionesActivas = m.pedidos_pendientes + m.pedidos_asignados + m.en_aire;
        $("badgeOperaciones").textContent = String(misionesActivas);
        $("badgeFlota").textContent = `${m.disponibles}/${m.total_flota}`;
        $("badgeDespacho").textContent = String(m.total_pedidos);
        $("badgeBitacora").textContent = String(m.total_logs);

        $("kpiDisponibles").textContent = String(m.disponibles);
        $("kpiEnVuelo").textContent = String(m.en_aire);
        $("kpiCompletados").textContent = String(m.pedidos_completados);
        $("kpiRelojSistema").textContent = `${Math.round(snapshot.reloj.tiempo_total_seg)}s`;
    }

    // ==========================================================================
    // ESPACIO 1: OPERACIONES, INDICADOR LINEAL Y SIMULACIÓN TEMPORAL
    // ==========================================================================

    function renderizarCabinaOperaciones(snapshot) {
        // 1. Cola operativa de misiones PENDIENTE y ASIGNADO
        const cola = snapshot.pedidos.filter((p) => ["PENDIENTE", "ASIGNADO", "EN_TRANSITO"].includes(p.estado));
        const contCola = $("opsQueueList");

        if (cola.length === 0) {
            contCola.innerHTML = `
                <div class="empty-state-box">
                    <p>No hay misiones pendientes ni en tránsito en este momento.</p>
                    <div class="queue-actions" style="justify-content: center;">
                        <button type="button" class="btn-secondary btn-sm" data-ir-vista="despacho">Crear Pedido</button>
                        <button type="button" class="btn-primary btn-sm" data-accion-tour="1">Ejecutar Tour E2E</button>
                    </div>
                </div>
            `;
        } else {
            contCola.innerHTML = cola
                .map((p) => {
                    const destinoTxt = p.direccion_destino || `(${p.coordenada_destino[0].toFixed(4)}, ${p.coordenada_destino[1].toFixed(4)})`;
                    let botones = "";
                    if (p.estado === "PENDIENTE") {
                        botones = `
                            <button type="button" class="btn-primary btn-sm" data-asignar-pedido="${escaparHtml(p.id_pedido)}">
                                Asignar Dron Compatible
                            </button>
                            <button type="button" class="btn-ghost btn-sm" data-cancelar-pedido="${escaparHtml(p.id_pedido)}">
                                Cancelar
                            </button>
                        `;
                    } else if (p.estado === "ASIGNADO") {
                        botones = `
                            <button type="button" class="btn-primary btn-sm" data-despegar-pedido="${escaparHtml(p.id_pedido)}" data-modo-desp="TEMPORAL">
                                Autorizar Despegue
                            </button>
                            <button type="button" class="btn-secondary btn-sm" data-despegar-pedido="${escaparHtml(p.id_pedido)}" data-modo-desp="INSTANTANEO" title="Ejecutar despacho completo síncrono">
                                Instantáneo
                            </button>
                        `;
                    } else if (p.estado === "EN_TRANSITO" && p.dron_asignado_id) {
                        botones = `
                            <button type="button" class="btn-secondary btn-sm" data-enfocar-cabina="${escaparHtml(p.dron_asignado_id)}">
                                Monitorear en Cabina
                            </button>
                        `;
                    }

                    return `
                        <div class="queue-item">
                            <div class="queue-top">
                                <span class="queue-id">${escaparHtml(p.id_pedido)}</span>
                                <span class="status-pill ${clasePildoraEstado(p.estado)}">${escaparHtml(p.estado)}</span>
                            </div>
                            <div class="queue-dest">${escaparHtml(destinoTxt)}</div>
                            <div class="queue-meta">
                                ${escaparHtml(p.categoria_etiqueta)} · Ida+Vuelta: ${p.distancia_ida_vuelta_km.toFixed(2)} km
                                ${p.dron_asignado_id ? ` · Dron: ${escaparHtml(p.dron_asignado_id)}` : ""}
                            </div>
                            <div class="queue-actions">${botones}</div>
                        </div>
                    `;
                })
                .join("");
        }

        // 2. Selector lateral de aeronaves en cabina
        const dronesEnTransito = snapshot.flota.filter((d) => d.en_vuelo_activo || d.retornando_a_base);
        $("opsActiveCountLabel").textContent = `${dronesEnTransito.length} en vuelo`;
        $("opsDroneSelectorList").innerHTML = snapshot.flota
            .map((d) => {
                const seleccionado = d.id_dron === estadoUI.dronCabinaId ? "is-selected" : "";
                let badgeHtml = "";
                if (d.en_vuelo_activo) {
                    badgeHtml = `<span class="drone-mini-tag tag-flight">EN VUELO</span>`;
                } else if (d.retornando_a_base) {
                    badgeHtml = `<span class="drone-mini-tag tag-return">RETORNO</span>`;
                } else if (!d.disponible) {
                    badgeHtml = `<span class="drone-mini-tag tag-busy">OCUPADO</span>`;
                } else {
                    badgeHtml = `<span class="drone-mini-tag tag-standby">BASE</span>`;
                }

                return `
                    <button type="button" class="drone-mini-item ${seleccionado}" data-enfocar-cabina="${escaparHtml(d.id_dron)}">
                        <div class="drone-mini-left">
                            <div class="drone-mini-title-row">
                                <strong>${escaparHtml(d.id_dron)}</strong>
                                ${badgeHtml}
                            </div>
                            <small>${escaparHtml(d.modelo_aeronave)} · ${escaparHtml(d.categoria_etiqueta)}</small>
                        </div>
                        <div class="drone-mini-right">
                            <div class="tabular-nums">${d.bateria.toFixed(1)}%</div>
                            <small>${escaparHtml(d.estado_operacional.replace(/_/g, " "))}</small>
                        </div>
                    </button>
                `;
            })
            .join("");

        // Tira de Flota en Tránsito Concurrente
        const stripContainer = $("concurrentFleetStrip");
        const chipsContainer = $("concurrentFleetChips");
        if (stripContainer && chipsContainer) {
            if (dronesEnTransito.length > 0) {
                stripContainer.classList.remove("is-hidden");
                chipsContainer.innerHTML = dronesEnTransito
                    .map((df) => {
                        const esFoco = df.id_dron === estadoUI.dronCabinaId;
                        const prog = df.progreso_lineal ? Math.round(df.progreso_lineal.progreso_ciclo_pct || 0) : 0;
                        const estadoCorto = df.retornando_a_base ? "Retorno" : "Vuelo";
                        return `
                            <button type="button" class="fleet-strip-chip ${esFoco ? "is-active" : ""}" data-enfocar-cabina="${escaparHtml(df.id_dron)}" title="Clic para enfocar telemetría de ${escaparHtml(df.id_dron)}">
                                <span class="chip-status-dot ${df.retornando_a_base ? "is-return" : "is-flight"}"></span>
                                <strong>${escaparHtml(df.id_dron)}</strong>
                                <span class="chip-meta">${estadoCorto} ${prog}% · ${df.bateria.toFixed(0)}%</span>
                            </button>
                        `;
                    })
                    .join("");
            } else {
                stripContainer.classList.add("is-hidden");
            }
        }

        // 3. Cabina principal del dron enfocado
        const dron = snapshot.flota.find((d) => d.id_dron === estadoUI.dronCabinaId) || snapshot.flota[0];
        if (!dron) return;

        const sesion = snapshot.sesiones_vuelo[dron.id_dron] || null;
        const progreso = dron.progreso_lineal || { fase_ciclo: "EN_PLATAFORMA", progreso_ciclo_pct: 0, etapa_actual: 0 };

        $("simEyebrow").textContent = `${dron.categoria_etiqueta} · ${dron.modelo_aeronave}`;
        const pill = $("simStatusPill");
        pill.textContent = dron.etiqueta_estado;
        pill.className = `status-pill ${clasePildoraEstado(dron.estado_operacional)}`;

        if (sesion) {
            $("simTitle").textContent = `${dron.id_dron} (${dron.modelo_aeronave}) · Misión ${sesion.id_pedido}`;
            $("simSubtitle").textContent =
                `Destino: ${sesion.direccion_destino} (${sesion.coordenadas_destino[0].toFixed(4)}, ${sesion.coordenadas_destino[1].toFixed(4)}) · ` +
                `Ida: ${Number(sesion.distancia_ida_total_km).toFixed(2)} km · Retorno: ${Number(sesion.distancia_retorno_total_km).toFixed(2)} km`;
        } else {
            $("simTitle").textContent = `${dron.id_dron} · ${dron.modelo_aeronave}`;
            $("simSubtitle").textContent =
                `Estacionado en Aeropuerto Olaya Herrera · Consumo nominal: ${dron.tasa_consumo_bat_km.toFixed(2)}% bat/km · Asigna y despega un pedido para simular.`;
        }

        $("simStatBateria").textContent = `${dron.bateria.toFixed(1)}%`;
        $("simStatAltitud").textContent = `${dron.altitud.toFixed(1)} m`;
        $("simStatVelocidad").textContent = `${dron.velocidad_efectiva_kmh.toFixed(1)} km/h`;
        $("simStatOdometro").textContent = `${dron.kilometraje_total_km.toFixed(2)} km`;

        // 4. Indicador Lineal Minimalista (Base -> Destino -> Retorno)
        const pct = Math.max(0, Math.min(100, Number(progreso.progreso_ciclo_pct) || 0));
        const emergencia = progreso.fase_ciclo === "EMERGENCIA_BATERIA" || dron.bateria <= 0;

        $("linearJourneyBox").classList.toggle("is-emergency", emergencia);
        $("journeyFill").style.width = `${pct}%`;
        $("journeyMarker").style.left = `${pct}%`;

        const nodoBase = $("stageNodeBase");
        const nodoDest = $("stageNodeDestino");
        const nodoRet = $("stageNodeRetorno");
        [nodoBase, nodoDest, nodoRet].forEach((n) => n.classList.remove("is-done", "is-current", "is-danger"));

        if (emergencia) {
            nodoBase.classList.add("is-done");
            if (pct < 50) {
                nodoDest.classList.add("is-danger");
            } else {
                nodoDest.classList.add("is-done");
                nodoRet.classList.add("is-danger");
            }
        } else if (progreso.etapa_actual === 0) {
            nodoBase.classList.add("is-current");
        } else if (progreso.etapa_actual === 1) {
            nodoBase.classList.add("is-done");
            nodoDest.classList.add("is-current");
        } else if (progreso.etapa_actual === 2) {
            nodoBase.classList.add("is-done");
            nodoDest.classList.add("is-done");
            nodoRet.classList.add("is-current");
        } else if (progreso.etapa_actual >= 3) {
            nodoBase.classList.add("is-done");
            nodoDest.classList.add("is-done");
            nodoRet.classList.add("is-done");
        }

        $("stageBaseCoords").textContent = `(${snapshot.coordenadas_base[0].toFixed(4)}, ${snapshot.coordenadas_base[1].toFixed(4)})`;
        if (sesion) {
            $("stageDestName").textContent = sesion.direccion_destino;
            $("stageDestMeta").textContent = progressDestSubtitle(sesion, progreso);
            $("stageReturnTitle").textContent = emergencia ? "Aterrizaje Forzoso (0.0%)" : "Retorno a Olaya Herrera";
            $("stageReturnMeta").textContent = emergencia
                ? `Interrumpido en (${dron.coordenadas[0].toFixed(4)}, ${dron.coordenadas[1].toFixed(4)})`
                : progreso.etapa_actual >= 3
                    ? "Completado · STANDBY · Disponible"
                    : `Tramo retorno: ${Number(sesion.distancia_retorno_total_km).toFixed(2)} km`;
        } else {
            $("stageDestName").textContent = "Sin destino activo";
            $("stageDestMeta").textContent = "Esperando asignación de pedido";
            $("stageReturnTitle").textContent = "Retorno a Plataforma";
            $("stageReturnMeta").textContent = "Motores en STANDBY";
        }

        $("simLiveGps").textContent = `(${dron.coordenadas[0].toFixed(5)}, ${dron.coordenadas[1].toFixed(5)})`;
        $("simLiveInstrument").textContent = sesion?.instrumental_activado || (dron.en_vuelo_activo ? "ACTIVO" : "EN ESPERA");
        $("simLiveRemaining").textContent = `${dron.distancia_objetivo_km.toFixed(2)} km`;
        $("simLiveElapsed").textContent = `${Number(sesion?.tiempo_acumulado_seg || 0).toFixed(1)} s`;

        // Habilitación de controles reales según estado físico de la aeronave
        const hayAlgunoEnVuelo = snapshot.flota.some((d) => d.en_vuelo_activo);
        $("btnAvanzarPulso").disabled = !dron.en_vuelo_activo && !hayAlgunoEnVuelo;
        document.querySelectorAll("[data-quick-delta]").forEach((b) => {
            b.disabled = !dron.en_vuelo_activo && !hayAlgunoEnVuelo;
        });
        $("btnOrdenarRetorno").disabled = !(dron.en_mision && dron.pedido_activo_id);
        $("btnAterrizarManual").classList.toggle("is-hidden", !dron.puede_aterrizar_manual);

        // Si estaba corriendo el reloj automático o de tiempo real y ya no queda ningún dron en vuelo, detenerlo limpiamente
        if (estadoUI.timerAuto && !hayAlgunoEnVuelo) {
            detenerAutoSimulacion();
        }
        if (estadoUI.timerRealtime && !hayAlgunoEnVuelo) {
            detenerSimulacionTiempoReal();
        }

        // 5. Tarjeta de Certificación Final
        const certBox = $("missionCertCard");
        if (sesion && sesion.certificacion_final && !dron.en_vuelo_activo) {
            const c = sesion.certificacion_final;
            certBox.classList.remove("is-hidden");
            certBox.classList.toggle("is-emergency", c.resultado === "EMERGENCIA_BATERIA");
            certBox.innerHTML = `
                <h4>${escaparHtml(c.titulo)}</h4>
                <div class="cert-grid">
                    <div><span>Tiempo Operación</span><strong>${c.tiempo_total_min} min (${c.tiempo_total_seg} s)</strong></div>
                    <div><span>Batería Remanente</span><strong>${c.bateria_final_pct.toFixed(1)}%</strong></div>
                    <div><span>Odómetro Acumulado</span><strong>${c.odometro_total_km.toFixed(2)} km</strong></div>
                    <div><span>Disponibilidad Dron</span><strong>${escaparHtml(c.disponibilidad_dron)}</strong></div>
                    <div><span>Estado del Pedido</span><strong>${escaparHtml(c.estado_pedido)}</strong></div>
                </div>
            `;
        } else {
            certBox.classList.add("is-hidden");
            certBox.innerHTML = "";
        }

        // 6. Tabla Cronológica de Pulsos
        const pulsos = sesion?.pulsos || [];
        $("pulseCountLabel").textContent = `${pulsos.length} ${pulsos.length === 1 ? "pulso registrado" : "pulsos registrados"}`;
        const tbody = $("pulseTableBody");

        if (pulsos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-cell">
                        ${
                            dron.en_vuelo_activo
                                ? "Aeronave en el aire a 30 m. Usa 'Avanzar Pulso' o 'Automática Animada' para integrar el movimiento."
                                : "Aún no hay pulsos temporales para esta aeronave. Registra/asigna un pedido y autoriza el despegue."
                        }
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = [...pulsos]
                .reverse()
                .map((p) => {
                    const claseFila =
                        p.estado === "BATERIA_AGOTADA"
                            ? "row-danger"
                            : ["LLEGADA_A_DESTINO", "LLEGADA_A_BASE"].includes(p.estado)
                                ? "row-highlight"
                                : "";
                    return `
                        <tr class="${claseFila}">
                            <td>${Number(p.t_seg).toFixed(0)} s <small>(+${Number(p.delta_t_seg).toFixed(0)}s)</small></td>
                            <td>${escaparHtml(p.fase)}</td>
                            <td>(${p.coordenadas[0].toFixed(4)}, ${p.coordenadas[1].toFixed(4)})</td>
                            <td>+${Number(p.delta_km).toFixed(2)} km</td>
                            <td>${Number(p.distancia_restante_km).toFixed(2)} km</td>
                            <td>${barraBateriaMiniHtml(p.bateria_pct)}</td>
                            <td><span class="status-pill ${clasePildoraEstado(p.estado)}">${escaparHtml(p.estado)}</span></td>
                        </tr>
                    `;
                })
                .join("");
        }
    }

    function progressDestSubtitle(sesion, progreso) {
        if (progreso.abortado) {
            return "Misión abortada (Retorno anticipado)";
        }
        if (progreso.etapa_actual >= 2) {
            return `Entregado · (${sesion.coordenadas_destino[0].toFixed(4)}, ${sesion.coordenadas_destino[1].toFixed(4)})`;
        }
        return `(${sesion.coordenadas_destino[0].toFixed(4)}, ${sesion.coordenadas_destino[1].toFixed(4)}) · ${Number(sesion.distancia_ida_total_km).toFixed(2)} km`;
    }

    // ==========================================================================
    // CONTROL DEL SIMULADOR TEMPORAL (PASO A PASO Y AUTOMÁTICO)
    // ==========================================================================

    function cambiarModoSimulacion(modo) {
        estadoUI.modoSimulacion = modo;
        $("btnModePaso").classList.toggle("is-active", modo === "paso");
        $("btnModeAuto").classList.toggle("is-active", modo === "auto");
        $("btnModeRealtime").classList.toggle("is-active", modo === "realtime");
        $("controlsPasoAPaso").classList.toggle("is-hidden", modo !== "paso");
        $("controlsAutomatico").classList.toggle("is-hidden", modo !== "auto");
        $("controlsTiempoReal").classList.toggle("is-hidden", modo !== "realtime");
        if (modo !== "auto" && estadoUI.timerAuto) {
            detenerAutoSimulacion();
        }
        if (modo !== "realtime" && estadoUI.timerRealtime) {
            detenerSimulacionTiempoReal();
        }
    }

    async function ejecutarPulsoSimulacion(deltaSeg, silencioso = false) {
        const snapshot = estadoUI.snapshot;
        if (!snapshot) return;

        const dronActual = snapshot.flota.find((d) => d.id_dron === estadoUI.dronCabinaId);
        // Simulación concurrente multidrón: id_dron null avanza todas las aeronaves en vuelo a la vez
        const idObjetivo = estadoUI.simularSoloEnfocado && dronActual && dronActual.en_vuelo_activo
            ? dronActual.id_dron
            : null;

        try {
            const nuevoEstado = await peticionAPI("/api/simulacion/paso", {
                metodo: "POST",
                cuerpo: {
                    id_dron: idObjetivo,
                    delta_t: Number(deltaSeg) || 30,
                    usar_reloj_real: false,
                },
            });
            aplicarSnapshot(nuevoEstado, !silencioso || Boolean(nuevoEstado.mensaje_operacion));
        } catch (_e) {
            if (estadoUI.timerAuto) detenerAutoSimulacion();
        }
    }

    function iniciarAutoSimulacion() {
        if (estadoUI.timerAuto) return;
        if (estadoUI.timerRealtime) {
            detenerSimulacionTiempoReal();
        }
        $("labelToggleAutoPlay").textContent = "Pausar Reloj Continuo";
        const ciclo = async () => {
            const salto = Number($("selectAutoDelta").value) || 25;
            await ejecutarPulsoSimulacion(salto, true);
        };
        ciclo();
        estadoUI.timerAuto = window.setInterval(ciclo, 620);
    }

    function detenerAutoSimulacion() {
        if (estadoUI.timerAuto) {
            window.clearInterval(estadoUI.timerAuto);
            estadoUI.timerAuto = null;
        }
        $("labelToggleAutoPlay").textContent = "Iniciar Reloj Continuo";
    }

    async function ejecutarPulsoTiempoReal(silencioso = true) {
        const snapshot = estadoUI.snapshot;
        if (!snapshot) return;

        const hayEnVuelo = snapshot.flota && snapshot.flota.some((d) => d.en_vuelo_activo);
        if (!hayEnVuelo) {
            detenerSimulacionTiempoReal();
            return;
        }

        const dronActual = snapshot.flota.find((d) => d.id_dron === estadoUI.dronCabinaId);
        const idObjetivo = estadoUI.simularSoloEnfocado && dronActual && dronActual.en_vuelo_activo
            ? dronActual.id_dron
            : null;

        const cadencia = Number($("selectRealtimeCadencia")?.value) || estadoUI.cadenciaRealtimeSeg || 5;

        try {
            const nuevoEstado = await peticionAPI("/api/simulacion/paso", {
                metodo: "POST",
                cuerpo: {
                    id_dron: idObjetivo,
                    delta_t: cadencia,
                    usar_reloj_real: true,
                    escala_tiempo: 1.0,
                },
            });
            aplicarSnapshot(nuevoEstado, !silencioso || Boolean(nuevoEstado.mensaje_operacion));
        } catch (_e) {
            detenerSimulacionTiempoReal();
        }
    }

    function iniciarSimulacionTiempoReal() {
        if (estadoUI.timerRealtime) return;
        if (estadoUI.timerAuto) {
            detenerAutoSimulacion();
        }

        const hayEnVuelo = estadoUI.snapshot?.flota?.some((d) => d.en_vuelo_activo);
        if (!hayEnVuelo) {
            mostrarNotificacion({
                tipo: "info",
                insignia: "TIEMPO REAL (1:1)",
                titulo: "Sin aeronaves en vuelo",
                mensaje: "Despega un dron o inicia una misión para observar el avance físico en tiempo real.",
            });
            return;
        }

        const cadenciaSeg = Number($("selectRealtimeCadencia")?.value) || 5;
        estadoUI.cadenciaRealtimeSeg = cadenciaSeg;

        $("labelToggleRealtimePlay").textContent = "Pausar Tiempo Real (1:1)";
        const btnFlota = $("btnTiempoRealFlota");
        if (btnFlota) {
            btnFlota.classList.add("is-running");
            $("labelTiempoRealFlota").textContent = `Tiempo Real Activo (${cadenciaSeg}s)`;
        }

        const ciclo = async () => {
            await ejecutarPulsoTiempoReal(true);
        };

        estadoUI.timerRealtime = window.setInterval(ciclo, cadenciaSeg * 1000);
    }

    function detenerSimulacionTiempoReal() {
        if (estadoUI.timerRealtime) {
            window.clearInterval(estadoUI.timerRealtime);
            estadoUI.timerRealtime = null;
        }
        $("labelToggleRealtimePlay").textContent = "Iniciar Tiempo Real (1:1)";
        const btnFlota = $("btnTiempoRealFlota");
        if (btnFlota) {
            btnFlota.classList.remove("is-running");
            $("labelTiempoRealFlota").textContent = "Tiempo Real (1:1)";
        }
    }

    // ==========================================================================
    // ESPACIO 2: FLOTA ACTIVA, INSPECTOR Y FÁBRICA DINÁMICA
    // ==========================================================================

    function renderizarFlotaEInspector(snapshot) {
        const grid = $("fleetCardsGrid");
        grid.innerHTML = snapshot.flota
            .map((d) => {
                const sel = d.id_dron === estadoUI.dronInspectorId ? "is-selected" : "";
                const specsHtml = d.especificaciones
                    .map((s) => `<span class="spec-chip">${escaparHtml(s.etiqueta)}: <strong>${escaparHtml(s.valor)}</strong></span>`)
                    .join("");
                return `
                    <div class="drone-card ${sel}" data-inspeccionar-dron="${escaparHtml(d.id_dron)}">
                        <div class="drone-card-head">
                            <div>
                                <strong>${escaparHtml(d.id_dron)}</strong>
                                <small>${escaparHtml(d.modelo_aeronave)} · ${escaparHtml(d.categoria_etiqueta)}</small>
                            </div>
                            <span class="status-pill ${clasePildoraEstado(d.estado_operacional)}">
                                ${escaparHtml(d.estado_operacional.replace(/_/g, " "))}
                            </span>
                        </div>

                        <div>${barraBateriaMiniHtml(d.bateria)}</div>

                        <div class="drone-specs-row">${specsHtml}</div>

                        <div class="drone-card-foot">
                            <span>${d.tasa_consumo_bat_km.toFixed(2)}% / km</span>
                            <span>${d.velocidad_promedio_kmh.toFixed(0)} km/h</span>
                            <span>${d.kilometraje_total_km.toFixed(2)} km acum.</span>
                        </div>
                    </div>
                `;
            })
            .join("");

        const dron = snapshot.flota.find((d) => d.id_dron === estadoUI.dronInspectorId) || snapshot.flota[0];
        if (!dron) return;

        $("inspDroneTitle").textContent = `${dron.id_dron} · ${dron.modelo_aeronave}`;
        const pill = $("inspDroneStatus");
        pill.textContent = dron.etiqueta_estado;
        pill.className = `status-pill ${clasePildoraEstado(dron.estado_operacional)}`;

        $("inspSystemsText").textContent = dron.diagnostico_sistemas;
        $("inspFichaStr").textContent = dron.ficha_str;
        $("inspFichaRepr").textContent = dron.ficha_repr;

        $("btnEjecutarRecarga").disabled = !dron.puede_recargar;

        // Historial inmutable de telemetría
        $("inspTeleCount").textContent = `${dron.total_tramas_telemetria} ${dron.total_tramas_telemetria === 1 ? "trama" : "tramas"}`;
        $("inspTeleHistory").innerHTML = [...dron.historial_telemetria]
            .reverse()
            .map((linea) => `<div class="immutable-item">${escaparHtml(linea)}</div>`)
            .join("");
    }

    function renderizarCamposDinamicosFabrica(categoria) {
        const esquema = estadoUI.snapshot?.esquema_fabrica?.[categoria];
        const cont = $("fabDynamicFields");
        if (!esquema) {
            cont.innerHTML = "";
            return;
        }

        $("fabModelo").value = esquema.modelo_sugerido || "";
        $("fabVelocidad").value = esquema.velocidad_default || 55;

        cont.innerHTML = esquema.campos
            .map((c) => {
                if (c.tipo === "bool") {
                    return `
                        <div class="field checkbox-field">
                            <input type="checkbox" id="fabParam_${escaparHtml(c.clave)}" data-fab-param="${escaparHtml(c.clave)}" ${c.default ? "checked" : ""}>
                            <label for="fabParam_${escaparHtml(c.clave)}">${escaparHtml(c.etiqueta)}</label>
                        </div>
                    `;
                }
                return `
                    <div class="field">
                        <label for="fabParam_${escaparHtml(c.clave)}">${escaparHtml(c.etiqueta)}</label>
                        <input
                            type="number"
                            id="fabParam_${escaparHtml(c.clave)}"
                            data-fab-param="${escaparHtml(c.clave)}"
                            min="${c.min ?? 0}"
                            max="${c.max ?? 99999}"
                            step="${c.step ?? 1}"
                            value="${c.default}"
                            required
                        >
                    </div>
                `;
            })
            .join("");
    }

    // ==========================================================================
    // ESPACIO 3: DESPACHO, GEOCODIFICACIÓN ARCGIS Y USUARIOS
    // ==========================================================================

    function renderizarDespachoYUsuarios(snapshot) {
        // Actualizar selector de usuario solicitante
        const selUsr = $("pedUsuario");
        const valorPrevio = selUsr.value || snapshot.usuario_activo.id_usuario;
        selUsr.innerHTML = snapshot.usuarios
            .map(
                (u) =>
                    `<option value="${escaparHtml(u.id_usuario)}">${escaparHtml(u.nombre)} (${escaparHtml(u.rol)})</option>`
            )
            .join("");
        if (snapshot.usuarios.some((u) => u.id_usuario === valorPrevio)) {
            selUsr.value = valorPrevio;
        }

        // Lista de usuarios registrados
        $("usersListContainer").innerHTML = snapshot.usuarios
            .map((u) => {
                const esActivo = u.id_usuario === snapshot.usuario_activo.id_usuario;
                return `
                    <div class="user-row ${esActivo ? "is-active" : ""}">
                        <div>
                            <strong>${escaparHtml(u.nombre)}</strong>
                            <small>${escaparHtml(u.id_usuario)} · Rol: ${escaparHtml(u.rol)}</small>
                        </div>
                        ${
                            esActivo
                                ? `<span class="status-pill pill-active">SESIÓN ACTIVA</span>`
                                : `<button type="button" class="btn-secondary btn-sm" data-activar-usuario="${escaparHtml(u.id_usuario)}">Usar Sesión</button>`
                        }
                    </div>
                `;
            })
            .join("");

        // Bandeja de pedidos filtrada
        const filtro = estadoUI.filtroPedidos;
        const pedidosFiltrados =
            filtro === "TODOS" ? snapshot.pedidos : snapshot.pedidos.filter((p) => p.estado === filtro);

        const contPedidos = $("ordersBoardList");
        if (pedidosFiltrados.length === 0) {
            contPedidos.innerHTML = `
                <div class="empty-state-box">
                    <p>
                        ${
                            snapshot.pedidos.length === 0
                                ? "Aún no hay pedidos registrados. Ingresa una dirección del Valle de Aburrá en el formulario izquierdo o inicia el Tour Guiado E2E."
                                : `No hay pedidos en el estado '${escaparHtml(filtro)}'.`
                        }
                    </p>
                </div>
            `;
            return;
        }

        contPedidos.innerHTML = pedidosFiltrados
            .map((p) => {
                const coordsTxt = p.coordenada_destino
                    ? `(${p.coordenada_destino[0].toFixed(5)}, ${p.coordenada_destino[1].toFixed(5)})`
                    : "Pendiente";
                const candidatosTxt =
                    p.candidatos && p.candidatos.length > 0
                        ? p.candidatos
                              .map(
                                  (c) =>
                                      `${c.id_dron}: ${c.bateria_actual_pct.toFixed(1)}% actual / ${c.consumo_ida_vuelta_pct.toFixed(1)}% req. (${c.elegible_ahora ? "Elegible" : "No elegible"})`
                              )
                              .join(" · ")
                        : "Sin aeronaves registradas para esta categoría.";

                let accionesHtml = "";
                if (p.estado === "PENDIENTE") {
                    accionesHtml = `
                        <button type="button" class="btn-primary btn-sm" data-asignar-pedido="${escaparHtml(p.id_pedido)}">
                            Asignar Dron Compatible
                        </button>
                        <button type="button" class="btn-danger-soft btn-sm" data-cancelar-pedido="${escaparHtml(p.id_pedido)}">
                            Cancelar Pedido
                        </button>
                    `;
                } else if (p.estado === "ASIGNADO") {
                    accionesHtml = `
                        <button type="button" class="btn-primary btn-sm" data-despegar-pedido="${escaparHtml(p.id_pedido)}" data-modo-desp="TEMPORAL">
                            Despegar e Ir a Simulador
                        </button>
                        <button type="button" class="btn-secondary btn-sm" data-despegar-pedido="${escaparHtml(p.id_pedido)}" data-modo-desp="INSTANTANEO">
                            Despacho Instantáneo
                        </button>
                        <button type="button" class="btn-danger-soft btn-sm" data-cancelar-pedido="${escaparHtml(p.id_pedido)}">
                            Cancelar Reserva
                        </button>
                    `;
                } else if (p.estado === "EN_TRANSITO" && p.dron_asignado_id) {
                    accionesHtml = `
                        <button type="button" class="btn-primary btn-sm" data-ir-cabina-dron="${escaparHtml(p.dron_asignado_id)}">
                            Ver Vuelo en Cabina
                        </button>
                    `;
                }

                return `
                    <div class="order-card">
                        <div class="order-card-top">
                            <div class="order-card-title">
                                <strong>${escaparHtml(p.id_pedido)}</strong>
                                <span class="rf-tag">${escaparHtml(p.categoria_etiqueta)}</span>
                                ${p.fuente_geocodificacion ? `<span class="mono-hint">${escaparHtml(p.fuente_geocodificacion)}</span>` : ""}
                            </div>
                            <span class="status-pill ${clasePildoraEstado(p.estado)}">${escaparHtml(p.estado)}</span>
                        </div>

                        <div class="order-grid-meta">
                            <div>
                                <span>Destino</span>
                                <strong>${escaparHtml(p.direccion_destino || "Coordenadas directas")}</strong>
                                <small class="mono">${escaparHtml(coordsTxt)}</small>
                            </div>
                            <div>
                                <span>Distancia Geodésica</span>
                                <strong class="mono">${p.distancia_ida_km.toFixed(2)} km ida · ${p.distancia_ida_vuelta_km.toFixed(2)} km total</strong>
                            </div>
                            <div>
                                <span>Carga y Solicitante</span>
                                <strong>${p.peso_carga_kg.toFixed(1)} kg · ${escaparHtml(p.usuario_nombre)}</strong>
                            </div>
                            <div>
                                <span>Aeronave Vinculada</span>
                                <strong class="mono">${escaparHtml(p.dron_asignado_id || "Sin asignar")}</strong>
                            </div>
                        </div>

                        <div class="candidate-hint">Autonomía ida+vuelta: ${escaparHtml(candidatosTxt)}</div>
                        ${accionesHtml ? `<div class="order-actions">${accionesHtml}</div>` : ""}
                    </div>
                `;
            })
            .join("");
    }

    // ==========================================================================
    // ESPACIO 4: COMPARADOR DE RENDIMIENTO ENERGÉTICO
    // ==========================================================================

    async function cargarComparativaPolimorfica(distanciaKm, sincronizarControles = true) {
        const dist = Math.max(1, Number(distanciaKm) || 15);
        estadoUI.distanciaPolimorfismoKm = dist;

        if (sincronizarControles) {
            $("inputPolyDist").value = dist;
            $("rangePolyDist").value = Math.min(60, dist);
        }

        const resp = await peticionAPI(`/api/polimorfismo/viabilidad?distancia_km=${encodeURIComponent(dist)}`);
        estadoUI.datosPolimorfismo = resp;

        $("polyBarsContainer").innerHTML = resp.resultados
            .map((r) => {
                const anchoPct = Math.min(100, r.consumo_estimado_pct);
                const excede = !r.mision_viable;
                return `
                    <div class="poly-bar-card">
                        <div class="poly-bar-top">
                            <strong>${escaparHtml(r.id_dron)}</strong>
                            <span>${r.consumo_estimado_pct.toFixed(1)}% cons.</span>
                        </div>
                        <small>${escaparHtml(r.categoria_etiqueta || r.tipo_dron)} · ${r.tasa_consumo_bat_km.toFixed(2)}% / km</small>
                        <div class="poly-meter">
                            <div class="poly-meter-fill ${excede ? "is-over" : ""}" style="width: ${anchoPct.toFixed(1)}%;"></div>
                        </div>
                        <small class="mono">Remanente: ${r.bateria_remanente_pct.toFixed(1)}% · ${r.mision_viable ? "VIABLE" : "NO VIABLE"}</small>
                    </div>
                `;
            })
            .join("");

        $("polyTableBody").innerHTML = resp.resultados
            .map(
                (r) => `
                    <tr>
                        <td class="mono"><strong>${escaparHtml(r.id_dron)}</strong><br><small>${escaparHtml(r.modelo_aeronave)}</small></td>
                        <td>${escaparHtml(r.categoria_etiqueta)}<br><small class="mono-hint">${escaparHtml(r.tipo_dron)}</small></td>
                        <td class="mono">${r.tasa_consumo_bat_km.toFixed(2)}% / km</td>
                        <td>${barraBateriaMiniHtml(r.bateria_actual_pct)}</td>
                        <td class="mono"><strong>${r.consumo_estimado_pct.toFixed(1)}%</strong></td>
                        <td class="mono">${r.bateria_remanente_pct.toFixed(1)}%</td>
                        <td>
                            <span class="status-pill ${r.mision_viable ? "pill-ok" : "pill-danger"}">
                                ${r.mision_viable ? "SÍ" : "NO"}
                            </span>
                        </td>
                        <td>${escaparHtml(r.diagnostico_autonomia)}</td>
                    </tr>
                `
            )
            .join("");
    }

    // ==========================================================================
    // ESPACIO 5: BITÁCORA DE AUDITORÍA Y REPORTE DE TORRE
    // ==========================================================================

    function renderizarBitacora(snapshot) {
        $("torreStrBox").textContent = snapshot.torre_str;
        $("torreReprBox").textContent = snapshot.torre_repr;

        const termino = ($("inputBuscarLog").value || "").trim().toLowerCase();
        const formato = $("selectFormatoLog").value;

        const filtrados = snapshot.logs.filter((l) => {
            if (!termino) return true;
            const bolsa = `${l.id_log} ${l.tipo_evento} ${l.id_dron || ""} ${l.id_pedido || ""} ${l.detalles}`.toLowerCase();
            return bolsa.includes(termino);
        });

        const usarTabla = formato === "tabla";
        $("auditTableContainer").classList.toggle("is-hidden", !usarTabla);
        $("auditRawContainer").classList.toggle("is-hidden", usarTabla);

        if (usarTabla) {
            $("auditTableBody").innerHTML =
                filtrados.length === 0
                    ? `<tr><td colspan="6" class="empty-cell">No hay registros que coincidan con el filtro actual.</td></tr>`
                    : filtrados
                          .map(
                              (l) => `
                                <tr>
                                    <td class="mono">${escaparHtml(l.id_log)}</td>
                                    <td class="mono">${escaparHtml(l.fecha_hora)}</td>
                                    <td><span class="status-pill ${clasePildoraEstado(l.tipo_evento)}">${escaparHtml(l.tipo_evento)}</span></td>
                                    <td class="mono">${escaparHtml(l.id_dron || "—")}</td>
                                    <td class="mono">${escaparHtml(l.id_pedido || "—")}</td>
                                    <td>${escaparHtml(l.detalles)}</td>
                                </tr>
                            `
                          )
                          .join("");
        } else {
            $("auditRawContainer").textContent =
                filtrados.length === 0
                    ? "Sin registros para mostrar."
                    : filtrados.map((l) => l.registro_formateado).join("\n" + "-".repeat(72) + "\n");
        }
    }

    // ==========================================================================
    // REGISTRO DE EVENTOS INTERACTIVOS
    // ==========================================================================

    function enlazarEventos() {
        // Conmutador de Tema (Modo Claro / Consola Oscura)
        const btnTema = $("btnToggleTheme");
        if (btnTema) {
            btnTema.addEventListener("click", () => {
                aplicarTema(estadoUI.tema === "dark" ? "light" : "dark");
            });
        }

        // Pestañas de espacios de trabajo
        document.querySelectorAll(".workspace-tab").forEach((btn) => {
            btn.addEventListener("click", () => cambiarVista(btn.dataset.view));
        });

        $("btnCloseFeedback").addEventListener("click", () => {
            $("feedbackBanner").classList.add("is-hidden");
        });

        $("btnIrUsuarios").addEventListener("click", () => {
            cambiarVista("despacho");
            $("cardGestionUsuarios").scrollIntoView({ behavior: "smooth", block: "start" });
        });

        $("btnNuevoPedidoRapido").addEventListener("click", () => {
            cambiarVista("despacho");
            $("pedDireccion").focus();
        });

        // Clima en vivo por nodo
        const consultarClimaActual = async () => {
            const nodo = $("selectNodoClima").value;
            const estado = await peticionAPI(`/api/clima?nodo=${encodeURIComponent(nodo)}`);
            aplicarSnapshot(estado, true);
        };
        $("btnConsultarClima").addEventListener("click", () => consultarClimaActual().catch(() => {}));
        $("selectNodoClima").addEventListener("change", () => consultarClimaActual().catch(() => {}));

        // Tour Guiado End-to-End (Opción 7 de ConsolaSkyRoute)
        $("btnIniciarTour").addEventListener("click", () => lanzarTourGuiado());

        // Controles de Simulación Temporal
        $("btnModePaso").addEventListener("click", () => cambiarModoSimulacion("paso"));
        $("btnModeAuto").addEventListener("click", () => cambiarModoSimulacion("auto"));
        $("btnModeRealtime").addEventListener("click", () => cambiarModoSimulacion("realtime"));

        $("btnToggleRealtimePlay").addEventListener("click", () => {
            if (estadoUI.timerRealtime) {
                detenerSimulacionTiempoReal();
            } else {
                iniciarSimulacionTiempoReal();
            }
        });

        $("btnTiempoRealFlota").addEventListener("click", () => {
            if (estadoUI.timerRealtime) {
                detenerSimulacionTiempoReal();
            } else {
                iniciarSimulacionTiempoReal();
            }
        });

        $("selectRealtimeCadencia").addEventListener("change", (ev) => {
            estadoUI.cadenciaRealtimeSeg = Number(ev.target.value) || 5;
            if (estadoUI.timerRealtime) {
                detenerSimulacionTiempoReal();
                iniciarSimulacionTiempoReal();
            }
        });

        $("btnAvanzarPulso").addEventListener("click", () => {
            const dt = Number($("inputDeltaT").value) || 30;
            ejecutarPulsoSimulacion(dt, false);
        });

        document.querySelectorAll("[data-quick-delta]").forEach((btn) => {
            btn.addEventListener("click", () => {
                const dt = Number(btn.dataset.quickDelta) || 30;
                $("inputDeltaT").value = dt;
                ejecutarPulsoSimulacion(dt, false);
            });
        });

        $("btnToggleAutoPlay").addEventListener("click", () => {
            if (estadoUI.timerAuto) {
                detenerAutoSimulacion();
            } else {
                iniciarAutoSimulacion();
            }
        });

        $("btnOrdenarRetorno").addEventListener("click", async () => {
            try {
                const resp = await peticionAPI("/api/misiones/retorno", {
                    metodo: "POST",
                    cuerpo: { id_dron: estadoUI.dronCabinaId },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("btnAterrizarManual").addEventListener("click", async () => {
            try {
                const resp = await peticionAPI("/api/misiones/aterrizar", {
                    metodo: "POST",
                    cuerpo: { id_dron: estadoUI.dronCabinaId },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("btnReiniciarReloj").addEventListener("click", async () => {
            try {
                const resp = await peticionAPI("/api/simulacion/reloj", {
                    metodo: "POST",
                    cuerpo: { accion: "reiniciar" },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        // Espacio 2: Flota, Fábrica, Recarga e Inyección de Telemetría
        $("btnSincronizarFlota").addEventListener("click", async () => {
            try {
                const resp = await peticionAPI("/api/flota/telemetria", {
                    metodo: "POST",
                    cuerpo: { accion: "refrescar_flota" },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("fabCategoria").addEventListener("change", (ev) => {
            renderizarCamposDinamicosFabrica(ev.target.value);
        });

        $("formFabricaDron").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const parametros = {};
            document.querySelectorAll("[data-fab-param]").forEach((el) => {
                const clave = el.dataset.fabParam;
                parametros[clave] = el.type === "checkbox" ? el.checked : Number(el.value);
            });

            try {
                const resp = await peticionAPI("/api/flota/fabrica", {
                    metodo: "POST",
                    cuerpo: {
                        categoria: $("fabCategoria").value,
                        id_dron: $("fabIdDron").value.trim(),
                        modelo_aeronave: $("fabModelo").value.trim(),
                        velocidad_promedio_kmh: Number($("fabVelocidad").value),
                        bateria_inicial: Number($("fabBateria").value),
                        parametros,
                    },
                });
                $("fabIdDron").value = "";
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("rangeRecarga").addEventListener("input", (ev) => {
            $("labelRecargaVal").textContent = `${ev.target.value}%`;
        });

        $("btnEjecutarRecarga").addEventListener("click", async () => {
            try {
                const resp = await peticionAPI("/api/flota/recargar", {
                    metodo: "POST",
                    cuerpo: {
                        id_dron: estadoUI.dronInspectorId,
                        porcentaje: Number($("rangeRecarga").value),
                    },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        document.querySelectorAll("[data-tele-preset]").forEach((btn) => {
            btn.addEventListener("click", () => {
                const preset = btn.dataset.telePreset;
                if (preset === "nominal") {
                    $("teleBat").value = 95;
                    $("teleAlt").value = 0;
                    $("teleMotores").value = "STANDBY";
                    $("teleLat").value = 6.2196;
                    $("teleLon").value = -75.5868;
                } else if (preset === "bateria_baja") {
                    $("teleBat").value = 12;
                    $("teleAlt").value = 0;
                    $("teleMotores").value = "STANDBY";
                    $("teleLat").value = 6.2196;
                    $("teleLon").value = -75.5868;
                } else if (preset === "error_altitud") {
                    $("teleBat").value = 80;
                    $("teleAlt").value = 145;
                    $("teleMotores").value = "EN_VUELO";
                    $("teleLat").value = 6.2196;
                    $("teleLon").value = -75.5868;
                } else if (preset === "error_aburra") {
                    $("teleBat").value = 85;
                    $("teleAlt").value = 30;
                    $("teleMotores").value = "EN_VUELO";
                    $("teleLat").value = 4.7110;
                    $("teleLon").value = -74.0721;
                }
            });
        });

        $("formTelemetriaManual").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            try {
                const resp = await peticionAPI("/api/flota/telemetria", {
                    metodo: "POST",
                    cuerpo: {
                        accion: "inyectar",
                        id_dron: estadoUI.dronInspectorId,
                        bateria: Number($("teleBat").value),
                        altitud: Number($("teleAlt").value),
                        estado_motores: $("teleMotores").value,
                        latitud: Number($("teleLat").value),
                        longitud: Number($("teleLon").value),
                    },
                });
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        // Espacio 3: Despacho, Geocodificación y Usuarios
        const fijarModoDestino = (modo) => {
            estadoUI.modoDestinoPedido = modo;
            $("btnModoDireccion").classList.toggle("is-active", modo === "direccion");
            $("btnModoCoordenadas").classList.toggle("is-active", modo === "coordenadas");
            $("bloqueDestinoDireccion").classList.toggle("is-hidden", modo !== "direccion");
            $("bloqueDestinoCoordenadas").classList.toggle("is-hidden", modo !== "coordenadas");
        };
        $("btnModoDireccion").addEventListener("click", () => fijarModoDestino("direccion"));
        $("btnModoCoordenadas").addEventListener("click", () => fijarModoDestino("coordenadas"));

        $("btnVerificarDireccion").addEventListener("click", async () => {
            const dir = $("pedDireccion").value.trim();
            if (!dir) {
                mostrarNotificacion({
                    tipo: "error",
                    insignia: "VALIDACIÓN",
                    titulo: "Dirección vacía",
                    mensaje: "Ingresa una dirección o punto de referencia en el Valle de Aburrá para verificar.",
                });
                return;
            }
            try {
                const det = await peticionAPI("/api/geocodificar", {
                    metodo: "POST",
                    cuerpo: { direccion: dir },
                });
                const card = $("geoPreviewCard");
                card.classList.remove("is-hidden");
                card.innerHTML = `
                    <strong>Coordenadas resueltas: <span class="mono">(${det.latitud.toFixed(6)}, ${det.longitud.toFixed(6)})</span></strong>
                    <span>Motor de resolución: <strong class="mono">${escaparHtml(det.fuente)}</strong> · Dentro del Valle de Aburrá</span>
                    <span>Distancia desde Olaya Herrera: <strong class="mono">${det.distancia_ida_km.toFixed(2)} km ida (${det.distancia_ida_vuelta_km.toFixed(2)} km ida+vuelta)</strong></span>
                `;
            } catch (_e) {
                $("geoPreviewCard").classList.add("is-hidden");
            }
        });

        $("formNuevoPedido").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const cuerpo = {
                id_pedido: $("pedIdOpcional").value.trim(),
                id_usuario: $("pedUsuario").value,
                categoria_requerida: $("pedCategoria").value,
                peso_carga_kg: Number($("pedPeso").value),
            };
            if (estadoUI.modoDestinoPedido === "direccion") {
                cuerpo.direccion_destino = $("pedDireccion").value.trim();
            } else {
                cuerpo.latitud = $("pedLatitud").value;
                cuerpo.longitud = $("pedLongitud").value;
            }

            try {
                const resp = await peticionAPI("/api/pedidos", {
                    metodo: "POST",
                    cuerpo,
                });
                $("pedIdOpcional").value = "";
                $("pedDireccion").value = "";
                $("geoPreviewCard").classList.add("is-hidden");
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("formNuevoUsuario").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            try {
                const resp = await peticionAPI("/api/usuarios", {
                    metodo: "POST",
                    cuerpo: {
                        accion: "registrar",
                        id_usuario: $("usrId").value.trim(),
                        nombre: $("usrNombre").value.trim(),
                        rol: $("usrRol").value,
                    },
                });
                $("usrId").value = "";
                $("usrNombre").value = "";
                aplicarSnapshot(resp, true);
            } catch (_e) {}
        });

        $("orderStateFilters").addEventListener("click", (ev) => {
            const btn = ev.target.closest("[data-order-filter]");
            if (!btn) return;
            estadoUI.filtroPedidos = btn.dataset.orderFilter;
            document.querySelectorAll("[data-order-filter]").forEach((b) => {
                b.classList.toggle("is-active", b.dataset.orderFilter === estadoUI.filtroPedidos);
            });
            if (estadoUI.snapshot) renderizarDespachoYUsuarios(estadoUI.snapshot);
        });

        // Espacio 4: Comparador de Rendimiento Energético
        $("inputPolyDist").addEventListener("change", (ev) => {
            cargarComparativaPolimorfica(ev.target.value, true).catch(() => {});
        });
        $("rangePolyDist").addEventListener("input", (ev) => {
            $("inputPolyDist").value = ev.target.value;
            cargarComparativaPolimorfica(ev.target.value, false).catch(() => {});
        });
        document.querySelectorAll("[data-poly-dist]").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll("[data-poly-dist]").forEach((b) => b.classList.remove("is-active"));
                btn.classList.add("is-active");
                cargarComparativaPolimorfica(Number(btn.dataset.polyDist), true).catch(() => {});
            });
        });

        // Espacio 5: Filtros de Bitácora
        $("inputBuscarLog").addEventListener("input", () => {
            if (estadoUI.snapshot) renderizarBitacora(estadoUI.snapshot);
        });
        $("selectFormatoLog").addEventListener("change", () => {
            if (estadoUI.snapshot) renderizarBitacora(estadoUI.snapshot);
        });

        // Delegación global de acciones dinámicas en tarjetas y listas
        document.addEventListener("click", async (ev) => {
            const btnSug = ev.target.closest("[data-dir-sugerida]");
            if (btnSug) {
                $("pedDireccion").value = btnSug.dataset.dirSugerida;
                $("btnVerificarDireccion").click();
                return;
            }

            const btnIrVista = ev.target.closest("[data-ir-vista]");
            if (btnIrVista) {
                cambiarVista(btnIrVista.dataset.irVista);
                return;
            }

            const btnTour = ev.target.closest("[data-accion-tour]");
            if (btnTour) {
                lanzarTourGuiado();
                return;
            }

            const btnEnfocar = ev.target.closest("[data-enfocar-cabina]");
            if (btnEnfocar) {
                estadoUI.dronCabinaId = btnEnfocar.dataset.enfocarCabina;
                if (estadoUI.snapshot) renderizarCabinaOperaciones(estadoUI.snapshot);
                return;
            }

            const btnIrCabina = ev.target.closest("[data-ir-cabina-dron]");
            if (btnIrCabina) {
                estadoUI.dronCabinaId = btnIrCabina.dataset.irCabinaDron;
                cambiarVista("operaciones");
                if (estadoUI.snapshot) renderizarCabinaOperaciones(estadoUI.snapshot);
                return;
            }

            const btnInsp = ev.target.closest("[data-inspeccionar-dron]");
            if (btnInsp) {
                estadoUI.dronInspectorId = btnInsp.dataset.inspeccionarDron;
                if (estadoUI.snapshot) {
                    const d = estadoUI.snapshot.flota.find((x) => x.id_dron === estadoUI.dronInspectorId);
                    if (d) {
                        $("teleBat").value = d.bateria;
                        $("teleAlt").value = d.altitud;
                        $("teleMotores").value = d.estado_motores;
                        $("teleLat").value = d.coordenadas[0];
                        $("teleLon").value = d.coordenadas[1];
                    }
                    renderizarFlotaEInspector(estadoUI.snapshot);
                }
                return;
            }

            const btnActivarUsr = ev.target.closest("[data-activar-usuario]");
            if (btnActivarUsr) {
                try {
                    const resp = await peticionAPI("/api/usuarios", {
                        metodo: "POST",
                        cuerpo: { accion: "cambiar", id_usuario: btnActivarUsr.dataset.activarUsuario },
                    });
                    aplicarSnapshot(resp, true);
                } catch (_e) {}
                return;
            }

            const btnAsignar = ev.target.closest("[data-asignar-pedido]");
            if (btnAsignar) {
                try {
                    const resp = await peticionAPI("/api/pedidos/asignar", {
                        metodo: "POST",
                        cuerpo: { id_pedido: btnAsignar.dataset.asignarPedido },
                    });
                    aplicarSnapshot(resp, true);
                } catch (_e) {}
                return;
            }

            const btnCancelar = ev.target.closest("[data-cancelar-pedido]");
            if (btnCancelar) {
                try {
                    const resp = await peticionAPI("/api/pedidos/cancelar", {
                        metodo: "POST",
                        cuerpo: { id_pedido: btnCancelar.dataset.cancelarPedido },
                    });
                    aplicarSnapshot(resp, true);
                } catch (_e) {}
                return;
            }

            const btnDespegar = ev.target.closest("[data-despegar-pedido]");
            if (btnDespegar) {
                const idPed = btnDespegar.dataset.despegarPedido;
                const modoDesp = btnDespegar.dataset.modoDesp || "TEMPORAL";
                try {
                    const resp = await peticionAPI("/api/misiones/despegar", {
                        metodo: "POST",
                        cuerpo: {
                            id_pedido: idPed,
                            modo_despacho: modoDesp,
                            actualizar_clima: true,
                        },
                    });
                    aplicarSnapshot(resp, true);
                    cambiarVista("operaciones");
                } catch (_e) {}
            }
        });
    }

    async function lanzarTourGuiado() {
        const btn = $("btnIniciarTour");
        btn.disabled = true;
        detenerAutoSimulacion();
        detenerSimulacionTiempoReal();
        cambiarVista("operaciones");

        try {
            const resp = await peticionAPI("/api/demo/preparar", { metodo: "POST", cuerpo: {} });
            aplicarSnapshot(resp, true);
            $("selectAutoDelta").value = "25";
            cambiarModoSimulacion("auto");
            iniciarAutoSimulacion();
        } catch (_e) {
        } finally {
            btn.disabled = false;
        }
    }

    // ==========================================================================
    // ARRANQUE INICIAL DE LA APLICACIÓN
    // ==========================================================================

    async function iniciar() {
        aplicarTema(estadoUI.tema);
        enlazarEventos();
        try {
            const estadoInicial = await peticionAPI("/api/estado");
            aplicarSnapshot(estadoInicial, false);
        } catch (_e) {}
    }

    document.addEventListener("DOMContentLoaded", iniciar);
})();
