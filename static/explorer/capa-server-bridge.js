/**
 * Bridge script to automatically load capa analysis data from sessionStorage
 * into the capa Explorer Web UI and add server integration buttons
 */

(function() {
    'use strict';

    // Get analysis data from sessionStorage
    const analysisData = sessionStorage.getItem('capaAnalysisData');
    const analysisId = sessionStorage.getItem('capaAnalysisId');

    // ============================================================================
    // Function Definitions
    // ============================================================================

    function addCapaServerButtons() {
        // Wait for the UI to be fully loaded
        setTimeout(() => {
            // Remove any existing button container
            const existing = document.getElementById('capa-server-actions');
            if (existing) existing.remove();

            // Create a button container
            const buttonContainer = document.createElement('div');
            buttonContainer.id = 'capa-server-actions';

            // Check if viewing an analysis or on home page
            const currentAnalysisId = sessionStorage.getItem('capaAnalysisId');

            // Position: centered for home, left-aligned for analysis view
            const containerStyle = currentAnalysisId ? `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            ` : `
                position: fixed;
                bottom: 40px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
                display: flex;
                justify-content: center;
                gap: 10px;
            `;

            buttonContainer.style.cssText = containerStyle;

            // Common button style matching Vuetify/Material Design
            const buttonStyle = `
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                font-family: Roboto, sans-serif;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                transition: all 0.2s;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            `;

            // If viewing an analysis, show Download JSON and Generate YARA buttons
            if (currentAnalysisId) {
                // Download JSON button
                const downloadBtn = document.createElement('button');
                downloadBtn.innerHTML = '';
                downloadBtn.style.cssText = buttonStyle + `
                    background: #1976d2;
                    color: white;
                `;
                downloadBtn.onmouseover = () => {
                    downloadBtn.style.background = '#1565c0';
                    downloadBtn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                };
                downloadBtn.onmouseout = () => {
                    downloadBtn.style.background = '#1976d2';
                    downloadBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                };
                downloadBtn.onclick = () => {
                    window.location.href = `/api/analyses/${currentAnalysisId}/download`;
                };
                buttonContainer.appendChild(downloadBtn);

                // Generate YARA button
                const yaraBtn = document.createElement('button');
                yaraBtn.innerHTML = '';
                yaraBtn.style.cssText = buttonStyle + `
                    background: #388e3c;
                    color: white;
                `;
                yaraBtn.onmouseover = () => {
                    yaraBtn.style.background = '#2e7d32';
                    yaraBtn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                };
                yaraBtn.onmouseout = () => {
                    yaraBtn.style.background = '#388e3c';
                    yaraBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                };
                yaraBtn.onclick = () => {
                    fetch('/api/info')
                        .then(r => r.json())
                        .then(data => {
                            if (!data.yara_generation_available) {
                                alert('YARA generation is not available on this server.');
                                return;
                            }
                            window.location.href = `/api/analyses/${currentAnalysisId}/generate-yara?min_confidence=medium&min_capabilities=2`;
                        })
                        .catch(err => {
                            console.error('Failed to check YARA availability:', err);
                            window.location.href = `/api/analyses/${currentAnalysisId}/generate-yara?min_confidence=medium&min_capabilities=2`;
                        });
                };
                buttonContainer.appendChild(yaraBtn);

                // Generate ClamAV button
                const clamavBtn = document.createElement('button');
                clamavBtn.innerHTML = '';
                clamavBtn.style.cssText = buttonStyle + `
                    background: #d32f2f;
                    color: white;
                `;
                clamavBtn.onmouseover = () => {
                    clamavBtn.style.background = '#c62828';
                    clamavBtn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                };
                clamavBtn.onmouseout = () => {
                    clamavBtn.style.background = '#d32f2f';
                    clamavBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                };
                clamavBtn.onclick = () => {
                    window.location.href = `/api/analyses/${currentAnalysisId}/generate-clamav?include_strings=true&string_count=10`;
                };
                buttonContainer.appendChild(clamavBtn);
            } else {
                // If on home page, show Upload to Server button
                const uploadServerBtn = document.createElement('button');
                uploadServerBtn.innerHTML = '';
                uploadServerBtn.style.cssText = buttonStyle + `
                    background: #f57c00;
                    color: white;
                `;
                uploadServerBtn.onmouseover = () => {
                    uploadServerBtn.style.background = '#e65100';
                    uploadServerBtn.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                };
                uploadServerBtn.onmouseout = () => {
                    uploadServerBtn.style.background = '#f57c00';
                    uploadServerBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                };
                uploadServerBtn.onclick = () => {
                    // Create a hidden file input
                    const fileInput = document.createElement('input');
                    fileInput.type = 'file';
                    fileInput.accept = '*';
                    fileInput.style.display = 'none';
                    fileInput.onchange = async (e) => {
                        const file = e.target.files[0];
                        if (!file) return;

                        uploadServerBtn.disabled = true;
                        uploadServerBtn.innerHTML = '';
                        uploadServerBtn.style.opacity = '0.6';

                        const formData = new FormData();
                        formData.append('file', file);

                        try {
                            const response = await fetch('/api/analyze', {
                                method: 'POST',
                                body: formData
                            });

                            const result = await response.json();

                            if (response.ok) {
                                uploadServerBtn.innerHTML = '';

                                // Wait for analysis to complete
                                const checkStatus = setInterval(async () => {
                                    const statusResp = await fetch(`/api/analyses/${result.analysis_id}`);
                                    const statusData = await statusResp.json();

                                    if (statusData.status === 'completed') {
                                        clearInterval(checkStatus);
                                        // Store data and reload
                                        sessionStorage.setItem('capaAnalysisData', JSON.stringify(statusData.results));
                                        sessionStorage.setItem('capaAnalysisId', result.analysis_id);
                                        window.location.reload();
                                    } else if (statusData.status === 'failed') {
                                        clearInterval(checkStatus);
                                        alert('Analysis failed: ' + statusData.error_message);
                                        uploadServerBtn.disabled = false;
                                        uploadServerBtn.innerHTML = '';
                                        uploadServerBtn.style.opacity = '1';
                                    }
                                }, 2000);
                            } else {
                                alert('Upload failed: ' + result.detail);
                                uploadServerBtn.disabled = false;
                                uploadServerBtn.innerHTML = '';
                                uploadServerBtn.style.opacity = '1';
                            }
                        } catch (error) {
                            alert('Upload error: ' + error.message);
                            uploadServerBtn.disabled = false;
                            uploadServerBtn.innerHTML = '';
                            uploadServerBtn.style.opacity = '1';
                        }

                        document.body.removeChild(fileInput);
                    };
                    document.body.appendChild(fileInput);
                    fileInput.click();
                };
                buttonContainer.appendChild(uploadServerBtn);
            }

            // Inject into the page
            document.body.appendChild(buttonContainer);

            console.log('[capa-server-bridge] Action buttons added to Explorer UI');
        }, 1000); // Wait 1 second for UI to stabilize
    }

    function waitForVueApp(callback, maxAttempts = 50) {
        let attempts = 0;

        const interval = setInterval(() => {
            attempts++;

            // Try to find the Vue app instance
            const vueApp = document.querySelector('#app')?.__vue_app__;

            if (vueApp || attempts >= maxAttempts) {
                clearInterval(interval);

                if (vueApp) {
                    console.log('[capa-server-bridge] Vue app found, loading data...');
                    callback();
                } else {
                    console.log('[capa-server-bridge] Vue app not found, trying alternative method...');
                    tryAlternativeLoad();
                }
            }
        }, 200);
    }

    function tryAlternativeLoad() {
        try {
            console.log('[capa-server-bridge] Attempting to load analysis data via global function...');

            // Wait for the global function to be available
            const checkGlobalFunction = setInterval(() => {
                if (typeof window.capaLoadAnalysisData === 'function') {
                    clearInterval(checkGlobalFunction);

                    // Call the global function exposed by the Vue app
                    const success = window.capaLoadAnalysisData(analysisData);

                    if (success) {
                        console.log('[capa-server-bridge] Analysis data loaded successfully via global function');

                        // Clear the sessionStorage after successful load
                        setTimeout(() => {
                            sessionStorage.removeItem('capaAnalysisData');
                            sessionStorage.removeItem('capaAnalysisId');
                        }, 1000);
                    } else {
                        console.error('[capa-server-bridge] Failed to load analysis data');
                    }
                }
            }, 100);

            // Timeout after 10 seconds
            setTimeout(() => {
                clearInterval(checkGlobalFunction);
                if (typeof window.capaLoadAnalysisData !== 'function') {
                    console.error('[capa-server-bridge] Timeout: Global capaLoadAnalysisData function not found');
                }
            }, 10000);

        } catch (error) {
            console.error('[capa-server-bridge] Error loading data:', error);
        }
    }

    function hideOriginalUploadButton() {
        /**
         * Hide the original "Upload from Local" button and intro text.
         *
         * The original capa-explorer has a built-in "Upload from Local" button that loads
         * pre-generated capa JSON files. We're hiding this to avoid confusion since we now
         * have the "Upload to Server" button for uploading actual malware binaries.
         *
         * To re-enable the original upload functionality:
         * 1. Comment out or remove the CSS rules below that hide .v-file-input and input[type="file"]
         * 2. The original upload button will reappear in the UI
         * 3. Users can then upload .json or .gz capa analysis files directly to the browser
         */

        // Run multiple times to catch dynamically loaded elements
        const hideAttempts = [500, 1000, 1500, 2000];

        hideAttempts.forEach(delay => {
            setTimeout(() => {
                // Inject CSS to hide original elements
                const existingStyle = document.getElementById('capa-hide-style');
                if (!existingStyle) {
                    const style = document.createElement('style');
                    style.id = 'capa-hide-style';
                    style.textContent = `
                        /* Hide the original upload from local button */
                        .v-file-input,
                        .v-file-input *,
                        input[type="file"],
                        label[for*="file"],
                        .v-input--file,
                        button.v-btn:has(input[type="file"]),
                        .v-btn:has(.v-file-input) {
                            display: none !important;
                            visibility: hidden !important;
                            opacity: 0 !important;
                            height: 0 !important;
                            width: 0 !important;
                        }

                        /* Hide the intro text/quick start section (but keep header/logo) */
                        .bg-blue-50 {
                            display: none !important;
                        }
                    `;
                    document.head.appendChild(style);
                }

                // Also hide elements using JavaScript (more aggressive)
                document.querySelectorAll('.v-file-input, input[type="file"], .v-input--file').forEach(el => {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    // Also hide parent elements
                    if (el.parentElement) el.parentElement.style.display = 'none';
                });

                // Hide intro paragraph
                const paragraphs = document.querySelectorAll('p');
                paragraphs.forEach(p => {
                    if (p.textContent.includes('capa Explorer Web is a web-based tool')) {
                        p.style.display = 'none';
                    }
                });

                // Hide "OR" text dividers
                document.querySelectorAll('div, span, p').forEach(el => {
                    const text = el.textContent.trim();
                    if ((text === 'OR' || text === 'or') && text.length <= 3) {
                        // Only hide if it's just "OR" text, not part of larger content
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                    }
                });

                console.log('[capa-server-bridge] Original upload button and intro text hidden (attempt at ' + delay + 'ms)');
            }, delay);
        });
    }

    async function displayAnalysisDashboard() {
        // Only show dashboard if no analysis is loaded (check sessionStorage directly)
        if (sessionStorage.getItem('capaAnalysisId')) {
            console.log('[capa-server-bridge] Analysis loaded, skipping dashboard');
            return;
        }

        // Check if dashboard already exists - don't create duplicates
        const existingDashboard = document.getElementById('capa-server-dashboard');
        if (existingDashboard) {
            console.log('[capa-server-bridge] Dashboard already exists, skipping');
            return;
        }

        console.log('[capa-server-bridge] Creating analysis dashboard');

        setTimeout(async () => {
            // Double-check conditions before actually creating
            if (sessionStorage.getItem('capaAnalysisId')) return;
            if (document.getElementById('capa-server-dashboard')) return;

            try {
                // Fetch recent analyses from server
                const response = await fetch('/api/analyses?limit=10');
                const data = await response.json();

                // Find the main content area - look for existing elements to position after
                // We want to place the dashboard AFTER the logo/header section
                let insertionPoint = null;
                let mainContent = null;

                // Try to find a good insertion point (after header/logo but before other content)
                // Look for common Vue/Vuetify container patterns
                const possibleContainers = [
                    document.querySelector('.v-main__wrap'),
                    document.querySelector('.v-container'),
                    document.querySelector('main'),
                    document.querySelector('#app > div > div'),
                    document.querySelector('#app')
                ];

                for (const container of possibleContainers) {
                    if (container) {
                        mainContent = container;
                        break;
                    }
                }

                if (!mainContent) {
                    console.log('[capa-server-bridge] Could not find main content area');
                    return;
                }

                // Create dashboard
                const dashboard = document.createElement('div');
                dashboard.id = 'capa-server-dashboard';
                dashboard.style.cssText = `
                    padding: 24px;
                    max-width: 1200px;
                    margin: 24px auto;
                `;

                // Add title
                const title = document.createElement('h1');
                title.textContent = 'Recent Analyses';
                title.style.cssText = `
                    font-size: 28px;
                    font-weight: 600;
                    margin-bottom: 24px;
                    color: #1e293b;
                `;
                dashboard.appendChild(title);

                // Add analyses list
                if (data.analyses && data.analyses.length > 0) {
                    data.analyses.forEach(analysis => {
                        const item = document.createElement('div');
                        item.style.cssText = `
                            background: white;
                            padding: 20px;
                            margin-bottom: 16px;
                            border-radius: 8px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                            cursor: pointer;
                            transition: all 0.2s;
                            border: 1px solid #e2e8f0;
                        `;
                        item.onmouseover = () => {
                            item.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                            item.style.transform = 'translateY(-2px)';
                        };
                        item.onmouseout = () => {
                            item.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                            item.style.transform = 'translateY(0)';
                        };
                        item.onclick = () => {
                            // Load this analysis
                            fetch(`/api/analyses/${analysis.id}`)
                                .then(r => r.json())
                                .then(data => {
                                    sessionStorage.setItem('capaAnalysisData', JSON.stringify(data.results));
                                    sessionStorage.setItem('capaAnalysisId', analysis.id);
                                    window.location.reload();
                                });
                        };

                        // Status badge
                        const statusColors = {
                            'completed': '#10b981',
                            'processing': '#f59e0b',
                            'failed': '#ef4444',
                            'pending': '#3b82f6'
                        };

                        item.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: start; gap: 16px;">
                                <div style="flex: 1;">
                                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1e293b;">
                                        ${analysis.filename}
                                    </div>
                                    <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                                        ${new Date(analysis.created_at).toLocaleString()} |
                                        ${(analysis.file_size / 1024).toFixed(2)} KB |
                                        Hash: ${analysis.file_hash.substring(0, 16)}...
                                        ${analysis.capabilities_count ? ` | ${analysis.capabilities_count} capabilities` : ''}
                                    </div>
                                    ${analysis.attack_techniques && analysis.attack_techniques.length > 0 ? `
                                        <div style="margin-top: 8px;">
                                            ${analysis.attack_techniques.map(tech =>
                                                `<span style="display: inline-block; background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px; margin-bottom: 4px;">${tech}</span>`
                                            ).join('')}
                                        </div>
                                    ` : ''}
                                </div>
                                ${analysis.status === 'completed' ? `
                                    <div style="display: flex; gap: 8px; align-items: center;">
                                        <button class="download-btn" data-id="${analysis.id}" style="
                                            padding: 6px 12px;
                                            border: none;
                                            border-radius: 4px;
                                            cursor: pointer;
                                            font-size: 12px;
                                            font-weight: 500;
                                            background: #1976d2;
                                            color: white;
                                            transition: all 0.2s;
                                            display: inline-flex;
                                            align-items: center;
                                            gap: 4px;
                                        " title="Download JSON">
                                             JSON
                                        </button>
                                        <button class="yara-btn" data-id="${analysis.id}" style="
                                            padding: 6px 12px;
                                            border: none;
                                            border-radius: 4px;
                                            cursor: pointer;
                                            font-size: 12px;
                                            font-weight: 500;
                                            background: #388e3c;
                                            color: white;
                                            transition: all 0.2s;
                                            display: inline-flex;
                                            align-items: center;
                                            gap: 4px;
                                        " title="Generate YARA Rule">
                                             YARA
                                        </button>
                                        <button class="clamav-btn" data-id="${analysis.id}" style="
                                            padding: 6px 12px;
                                            border: none;
                                            border-radius: 4px;
                                            cursor: pointer;
                                            font-size: 12px;
                                            font-weight: 500;
                                            background: #d32f2f;
                                            color: white;
                                            transition: all 0.2s;
                                            display: inline-flex;
                                            align-items: center;
                                            gap: 4px;
                                        " title="Generate ClamAV Signatures">
                                             ClamAV
                                        </button>
                                    </div>
                                ` : ''}
                            </div>
                        `;

                        // Add event listeners for action buttons (if completed)
                        if (analysis.status === 'completed') {
                            const downloadBtn = item.querySelector('.download-btn');
                            const yaraBtn = item.querySelector('.yara-btn');
                            const clamavBtn = item.querySelector('.clamav-btn');

                            if (downloadBtn) {
                                downloadBtn.onclick = (e) => {
                                    e.stopPropagation(); // Prevent triggering item click
                                    window.location.href = `/api/analyses/${analysis.id}/download`;
                                };
                                downloadBtn.onmouseover = (e) => {
                                    e.target.style.background = '#1565c0';
                                    e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                                };
                                downloadBtn.onmouseout = (e) => {
                                    e.target.style.background = '#1976d2';
                                    e.target.style.boxShadow = 'none';
                                };
                            }

                            if (yaraBtn) {
                                yaraBtn.onclick = (e) => {
                                    e.stopPropagation(); // Prevent triggering item click
                                    fetch('/api/info')
                                        .then(r => r.json())
                                        .then(data => {
                                            if (!data.yara_generation_available) {
                                                alert('YARA generation is not available on this server.');
                                                return;
                                            }
                                            window.location.href = `/api/analyses/${analysis.id}/generate-yara?min_confidence=medium&min_capabilities=2`;
                                        })
                                        .catch(err => {
                                            console.error('Failed to check YARA availability:', err);
                                            window.location.href = `/api/analyses/${analysis.id}/generate-yara?min_confidence=medium&min_capabilities=2`;
                                        });
                                };
                                yaraBtn.onmouseover = (e) => {
                                    e.target.style.background = '#2e7d32';
                                    e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                                };
                                yaraBtn.onmouseout = (e) => {
                                    e.target.style.background = '#388e3c';
                                    e.target.style.boxShadow = 'none';
                                };
                            }

                            if (clamavBtn) {
                                clamavBtn.onclick = (e) => {
                                    e.stopPropagation(); // Prevent triggering item click
                                    window.location.href = `/api/analyses/${analysis.id}/generate-clamav?include_strings=true&string_count=10`;
                                };
                                clamavBtn.onmouseover = (e) => {
                                    e.target.style.background = '#c62828';
                                    e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                                };
                                clamavBtn.onmouseout = (e) => {
                                    e.target.style.background = '#d32f2f';
                                    e.target.style.boxShadow = 'none';
                                };
                            }
                        }

                        dashboard.appendChild(item);
                    });
                } else {
                    const emptyState = document.createElement('div');
                    emptyState.style.cssText = `
                        text-align: center;
                        padding: 60px 20px;
                        color: #64748b;
                        max-width: 800px;
                        margin: 0 auto;
                    `;
                    emptyState.innerHTML = `
                        <div style="font-size: 64px; margin-bottom: 24px;"></div>
                        <div style="font-size: 24px; font-weight: 600; margin-bottom: 16px; color: #1e293b;">
                            Welcome to capa-server
                        </div>
                        <div style="font-size: 16px; margin-bottom: 32px; line-height: 1.6; color: #475569;">
                            Automated malware capability analysis powered by capa
                        </div>

                        <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 32px; margin-bottom: 24px;">
                            <div style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1e293b;">
                                Get Started
                            </div>
                            <div style="font-size: 14px; margin-bottom: 20px; color: #64748b; line-height: 1.6;">
                                Click the <strong>"Upload to Server"</strong> button below to analyze your first malware sample.
                                <br>capa will automatically detect capabilities, behaviors, and MITRE ATT&CK techniques.
                            </div>

                            <div style="display: inline-block; text-align: left; margin-top: 16px;">
                                <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px; color: #475569;">
                                     Supported Formats:
                                </div>
                                <div style="font-size: 13px; color: #64748b; line-height: 1.8;">
                                    • <strong>PE</strong> (Portable Executable): Windows .exe, .dll, .sys<br>
                                    • <strong>ELF</strong> (Executable and Linkable Format): Linux binaries<br>
                                    • <strong>Mach-O</strong>: macOS binaries<br>
                                    • <strong>.NET</strong>: Managed assemblies<br>
                                    • <strong>Shellcode</strong>: Raw binary shellcode (32-bit/64-bit)
                                </div>
                            </div>
                        </div>

                        <div style="font-size: 13px; color: #94a3b8;">
                             After analysis completes, you can download results as JSON or generate YARA detection rules
                        </div>
                    `;
                    dashboard.appendChild(emptyState);
                }

                // Append dashboard to main content (will appear after header/logo)
                mainContent.appendChild(dashboard);

                console.log('[capa-server-bridge] Analysis dashboard displayed');
            } catch (error) {
                console.error('[capa-server-bridge] Failed to load dashboard:', error);
            }
        }, 1500); // Wait a bit longer for the Vue app to render
    }

    function setupHomeReloadHandler() {
        /**
         * Intercept clicks on the home icon/link and force a full page reload.
         * This ensures clean state when returning to the home page.
         */

        // Try multiple times to find and attach to the home link (Vue loads it dynamically)
        const retryDelays = [500, 1000, 1500, 2000, 3000];

        retryDelays.forEach(delay => {
            setTimeout(() => {
                // Find all links that point to home
                const homeLinks = document.querySelectorAll('a[href="#/"], a[href="#"], a[href="/"]');

                homeLinks.forEach(link => {
                    // Check if we already attached the listener
                    if (!link.dataset.capaHomeListener) {
                        link.dataset.capaHomeListener = 'true';
                        link.addEventListener('click', (e) => {
                            console.log('[capa-server-bridge] Home link clicked - clearing and reloading');
                            e.preventDefault();
                            e.stopPropagation();

                            // Clear any analysis data
                            sessionStorage.removeItem('capaAnalysisData');
                            sessionStorage.removeItem('capaAnalysisId');

                            // Reload the page to get clean state
                            window.location.href = window.location.pathname;
                        }, true); // Use capture phase to intercept before Vue router

                        console.log('[capa-server-bridge] Attached reload handler to home link');
                    }
                });
            }, delay);
        });
    }

    function setupRouteChangeHandler() {
        /**
         * Monitor for route changes and re-apply customizations.
         */

        // Listen for hash changes (Vue Router uses hash mode)
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash;
            console.log('[capa-server-bridge] Route change detected:', hash);

            // Re-apply UI customizations with multiple retry attempts
            const retryDelays = [500, 1000, 1500, 2000];

            retryDelays.forEach(delay => {
                setTimeout(() => {
                    console.log(`[capa-server-bridge] Applying customizations (attempt at ${delay}ms)`);
                    hideOriginalUploadButton();
                    addCapaServerButtons();
                }, delay);
            });
        });

        // Also watch for DOM mutations (Vue re-rendering)
        const observer = new MutationObserver((mutations) => {
            // Check if original upload button has reappeared
            const uploadButton = document.querySelector('input[type="file"]');

            if (uploadButton) {
                console.log('[capa-server-bridge] Original upload button detected, re-hiding');
                hideOriginalUploadButton();

                // If we're on home and dashboard is missing, recreate it
                if ((window.location.hash === '#/' || window.location.hash === '') &&
                    !document.getElementById('capa-server-dashboard')) {
                    console.log('[capa-server-bridge] Dashboard missing on home, recreating');
                    displayAnalysisDashboard();
                }
            }
        });

        // Observe the main app container
        const appContainer = document.querySelector('#app');
        if (appContainer) {
            observer.observe(appContainer, {
                childList: true,
                subtree: true
            });
        }

        console.log('[capa-server-bridge] Route change handler installed');
    }

    // ============================================================================
    // Execution
    // ============================================================================

    // Hide original UI elements
    hideOriginalUploadButton();

    // Always add the server buttons
    addCapaServerButtons();

    // Display dashboard or load analysis
    if (analysisData) {
        console.log(`[capa-server-bridge] Found analysis data for ID: ${analysisId}`);
        waitForVueApp(() => {
            tryAlternativeLoad();
        });
    } else {
        console.log('[capa-server-bridge] No analysis data found in sessionStorage');
        displayAnalysisDashboard();
    }

    // Setup route change monitoring
    setupRouteChangeHandler();

    // Setup home link reload handler
    setupHomeReloadHandler();

})();
