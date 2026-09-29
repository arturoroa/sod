import { getSessionData } from "./storage";

export const url = import.meta.env.VITE_BACKEND_URL;
//export const url = 'http://localhost:5678';
const debugFront = String(import.meta.env.VITE_DEBUG_FRONT ?? 'true').toLowerCase() === 'true';

const getTraceId = () => `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

const normalizeTracePayload = (payload: any): any => {
    if (payload instanceof Error) {
        const errorPayload: any = {
            type: 'Error',
            name: payload.name,
            message: payload.message,
            stack: payload.stack,
        };
        Object.getOwnPropertyNames(payload).forEach((key) => {
            if (!['name', 'message', 'stack'].includes(key)) {
                errorPayload[key] = (payload as any)[key];
            }
        });
        return errorPayload;
    }
    if (payload instanceof Blob) {
        return { type: 'Blob', size: payload.size, mimeType: payload.type };
    }
    if (payload instanceof FormData) {
        const entries: any[] = [];
        payload.forEach((value, key) => {
            entries.push({ key, value: value instanceof File ? value.name : String(value) });
        });
        return { type: 'FormData', entries };
    }
    if (Array.isArray(payload)) {
        return payload.map(normalizeTracePayload);
    }
    if (payload && typeof payload === 'object') {
        const normalized: any = {};
        Object.entries(payload).forEach(([key, value]) => {
            normalized[key] = normalizeTracePayload(value);
        });
        return normalized;
    }
    return payload;
};

const sendTraceToTerminal = (traceId: string, step: string, payload?: any) => {
    if (!debugFront) return;
    try {
        const tracePayload = {
            traceId,
            step,
            payload: normalizeTracePayload(payload),
            source: 'generalService',
        };
        const text = JSON.stringify(tracePayload);
        if (navigator.sendBeacon) {
            const blob = new Blob([text], { type: 'application/json' });
            navigator.sendBeacon('/__front_trace', blob);
            return;
        }
        fetch('/__front_trace', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: text,
            keepalive: true,
        }).catch(() => {});
    } catch {
        // Intentionally ignore trace transport failures.
    }
};

const summarizeBody = (body: any) => {
    if (body == null) return null;
    if (body instanceof FormData) {
        const entries: any[] = [];
        body.forEach((value, key) => {
            if (value instanceof File) {
                entries.push({ key, fileName: value.name, type: value.type, size: value.size });
            } else {
                entries.push({ key, value: String(value).slice(0, 300) });
            }
        });
        return { type: 'FormData', entries };
    }
    if (body instanceof Blob) {
        return { type: 'Blob', size: body.size };
    }
    if (typeof body === 'string') {
        return body.length > 1000 ? `${body.slice(0, 1000)}... [truncated]` : body;
    }
    return body;
};

const logStep = (traceId: string, step: string, payload?: any) => {
    if (!debugFront) return;
    const now = new Date().toISOString();
    sendTraceToTerminal(traceId, step, payload);
    if (payload !== undefined) {
        console.log(`[FRONT][${now}][${traceId}] ${step}`, payload);
        return;
    }
    console.log(`[FRONT][${now}][${traceId}] ${step}`);
};

const header = {
    'Content-Type': 'application/json'
}

const handleError = (error: any, url?: string) => {
    let errorMessage = '';
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
        errorMessage = `Failed to fetch ${url ?? ''}`.trim();
    } else if (error.error instanceof ErrorEvent) {
        errorMessage = error.error.message;
    } else {
        errorMessage = `Error code: ${error.status}\n Message: ${error.message}`;
    }
    window.alert(errorMessage);
}

const delay = (ms:number) => new Promise((resolve) => setTimeout(resolve, ms));

const fetchWithRetry = async (finalUrl:string, options:any, retries = 2, delayMs = 300) => {
    let lastError:any = null;
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            return await fetch(finalUrl, options);
        } catch (error) {
            lastError = error;
            if (attempt < retries) {
                await delay(delayMs);
            }
        }
    }
    throw lastError;
};

export const httpRequest = async (method:string, endpoint:string, body:any = null, headers:any = null) => {
    const traceId = getTraceId();
    const startedAt = performance.now();
    const finalUrl = `${url}${endpoint}`;
    logStep(traceId, 'HTTP_REQUEST_START', { method, endpoint, baseUrl: url, finalUrl });
    try{
        const options:any = {}
        options['method'] = method;
        options['mode'] = 'cors';
        options['cache'] = 'no-store';
        if (headers == null){
            options['headers'] = header;
        }
        if (headers != null && headers != true){
            options['headers'] = headers
        }
        if (body){
            if (headers != true && options['headers']['Content-Type']=='application/json'){
                options['body'] = JSON.stringify(body);
            }else{
                options['body'] = body;
            }
        }
        logStep(traceId, 'HTTP_REQUEST_OPTIONS_READY', {
            method: options.method,
            headers: options.headers,
            body: summarizeBody(options.body),
        });

        const response = await fetchWithRetry(finalUrl, options);
        const durationMs = Number((performance.now() - startedAt).toFixed(2));
        logStep(traceId, 'HTTP_RESPONSE_RECEIVED', {
            status: response.status,
            ok: response.ok,
            durationMs,
            contentType: response.headers.get('Content-Type'),
            contentDisposition: response.headers.get('Content-Disposition'),
        });
        
        if (response.ok) {
            const contentType = response.headers.get('Content-Type');
            const contentDisposition = response.headers.get('Content-Disposition');
            
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                logStep(traceId, 'HTTP_RESPONSE_JSON', data);
                return data;
            }

            if (contentType && contentType.includes('application/zip')) {
                const data:any = {};
                if (contentDisposition && contentDisposition.includes('filename')){
                    data['name'] = contentDisposition.split('"')[1].trim();
                }
                data['blob'] = await response.blob();
                logStep(traceId, 'HTTP_RESPONSE_ZIP', { name: data.name, blobSize: data.blob?.size ?? null });
                return data;
            }

            if (contentType && contentType.includes('text/html')) {
                const html = await response.text();
                logStep(traceId, 'HTTP_RESPONSE_HTML', { length: html.length });
                return html;
            }
            logStep(traceId, 'HTTP_RESPONSE_UNHANDLED_CONTENT_TYPE', { contentType });
        } else {
            const errorData = await response.json();
            logStep(traceId, 'HTTP_RESPONSE_ERROR_JSON', errorData);
            return errorData;
        }
    } catch(error){
        logStep(traceId, 'HTTP_REQUEST_EXCEPTION', error);
        handleError(error, `${url}${endpoint}`);
        return null;
    }
}

export const upload = async (endpoint:string, fileOrDocument: any, body:any = null) =>{
    const traceId = getTraceId();
    logStep(traceId, 'UPLOAD_START', { endpoint });
    const result:any = {};
    result['status'] = 'ERROR';
    try{
        const formData = new FormData();

        let fileToUpload: File | null = null;

        if (fileOrDocument instanceof File) {
            fileToUpload = fileOrDocument;
        } else if (fileOrDocument?.assets?.[0]?.file instanceof File) {
            fileToUpload = fileOrDocument.assets[0].file;
        } else if (fileOrDocument?.assets?.[0]?.uri) {
            const blobResponse = await fetch(fileOrDocument.assets[0].uri);
            const blob = await blobResponse.blob();
            fileToUpload = new File([blob], fileOrDocument.assets[0].name || 'upload.bin', { type: blob.type });
        }

        if (!fileToUpload) {
            throw new Error('Invalid file payload');
        }

        logStep(traceId, 'UPLOAD_FILE_READY', {
            fileName: fileToUpload.name,
            fileType: fileToUpload.type,
            fileSize: fileToUpload.size,
        });

        formData.append('file', fileToUpload, fileToUpload.name);
        if (body){
            formData.append('session', JSON.stringify(body))
        }
        const response = await httpRequest('POST', endpoint, formData, true);
        if (response && response.Result){
            result['status'] = 'OK';
        }
        result['response'] = response;
        logStep(traceId, 'UPLOAD_FINISHED', { status: result.status, response });
    }catch(e){
        result['response'] = e;
        logStep(traceId, 'UPLOAD_EXCEPTION', e);
    }
    return result;
}

export const download = async (isDisabled:boolean, setIsDisabled:(value:boolean)=>void, endpoint:string) => {
    const traceId = getTraceId();
    logStep(traceId, 'DOWNLOAD_START', { endpoint, isDisabled });
    if (!isDisabled){
        const sessionData = await getSessionData();
        logStep(traceId, 'DOWNLOAD_SESSION_DATA', sessionData);
        if (sessionData && sessionData.Company){
            setIsDisabled(true)
            //setIsLoading(true)
            const response = await httpRequest('POST', endpoint, sessionData);
            if (response && response?.Result == undefined){
                const dlUrl = window.URL.createObjectURL(response.blob);
                const a = document.createElement("a");
                a.href = dlUrl;
                a.setAttribute("download", response.name);
                a.click();
                window.URL.revokeObjectURL(dlUrl);
                logStep(traceId, 'DOWNLOAD_FILE_TRIGGERED', { fileName: response.name, blobSize: response?.blob?.size ?? null });
            }else{
                window.alert(response?.Result)
                logStep(traceId, 'DOWNLOAD_SERVER_RESULT', response);
            }
            setIsDisabled(false)
            logStep(traceId, 'DOWNLOAD_FINISHED');
        }
    }else{
        console.log('Disable Download')
        logStep(traceId, 'DOWNLOAD_SKIPPED_DISABLED');
    }
}

export const checkStatus = async (sessionData:any, setMenuStatus:(value:boolean)=>void) => {
    const traceId = getTraceId();
    logStep(traceId, 'CHECK_STATUS_START', sessionData);
    if (sessionData && sessionData.Company){
        const value = await httpRequest('POST', '/is_report_active', sessionData);
        logStep(traceId, 'CHECK_STATUS_RESPONSE', value);
        if (value && value.Result==1){
            setMenuStatus(true);
            logStep(traceId, 'CHECK_STATUS_ACTIVE_TRUE');
            return true;
        }
        if (value && value.Result==-1){
            setMenuStatus(false);
            logStep(traceId, 'CHECK_STATUS_ACTIVE_FALSE');
            return false;
        }
    }
};

