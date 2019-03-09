import axios from 'axios';
import { MapperService } from './MapperService';
import Logger from '../logger';
import { ServerExceptionModel } from '../models/ServerExceptionModel';

export class RequestService {
    constructor(url) {
        this._serverUrl = `http://${url}`;
        axios.defaults.validateStatus = function (status) {
            return status <= 500; // Reject only if the status code is greater than 500
        }
    }

    _changeHostUrl(url) {
        this._serverUrl = `http://${url}`;
    }

    _constructPath(route, anotherUrl = null) {
        if (!anotherUrl) {
            return `${this._serverUrl}/${route}`;
        } else {
            return `http://${anotherUrl}/${route}`;
        }
    }

    _deleteAuthHeader() {
        Logger.info(`Deleting auth token`);
        delete axios.defaults.headers.common['authorization'];
    }

    _setAuthHeader(token) {
        Logger.info(`Setting new token ${token}`);
        axios.defaults.headers.common['authorization'] = token;
    }

    async _authorize(password) {
        const path = this._constructPath(`api/login`);
        const result = await axios.post(path, { password });
        console.log(result.status);
        if (result.status === 200) {
            const body = result.data;
            return body.token;
        } else {
            // TODO Log normal. + Unauth
            Logger.info(result.data.errorInfo);
            throw new ServerExceptionModel(result.data.errorInfo, result.status);
            // Logger.error(result);
            // return false;
        }
    }

    async _deauthorize() {
        const path = this._constructPath(`api/logout`);
        const result = await axios.get(path);
        console.log(result.status);
        if (result.status === 200) {
            return true;
        } else {
            Logger.error(result.data.errorInfo);
            throw new ServerExceptionModel(result.data.errorInfo, result.status);
        }
    }

    async _changePassword(oldPassword, newPassword) {
        const path = this._constructPath(`api/password`);
        const res = await axios.post(path, { oldPassword, newPassword });
        if (res.status === 200) {
            const body = res.data;
            return body.token;
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async getHealth(url = null) {
        const path = this._constructPath('api/utils/health', url);
        try {
            const res = await axios.get(path, { timeout: 1000 });
            return res.status === 200 && res.data.code === 0;
        } catch (e) {
            return false;
        }
    }

    async getNetworks() {
        const path = this._constructPath('api/wifi');
        const res = await axios.get(path);
        if (res.status === 200) {
            return MapperService.mapNetworksResponse(res.data);
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async getModules() {
        const path = this._constructPath('api/modules');
        const res = await axios.get(path);
        if (res.status === 200) {
            return res.data;
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async changeNetwork(name, password) {
        const path = this._constructPath('api/wifi/connect');
        const res = await axios.post(path, { name, password });
        if (res.status === 200) {
            return true
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async getCoreConfig() {
        const path = this._constructPath('api/config');
        const res = await axios.get(path);
        if (res.status === 200) {
            return res.data;
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async setCoreConfig(newConfig) {
        const path = this._constructPath('api/config');
        const res = await axios.post(path, newConfig);
        if (res.status === 200) {
            // TODO change answer format in backend
            return true;
        } else {
            Logger.error(res.data.errorInfo);
            throw new ServerExceptionModel(res.data.errorInfo, res.status);
        }
    }

    async getLogs(robotName, limit = 1, offset = 0, startTime = null, endTime = null, type = null, sortByTime = null, sortByType = null) {
        const path = this._constructPath(`api/monitoring/logs/${robotName}`);

        const body = {};
        body['filter'] = {}
        body['sort'] = {}
        if (startTime != null) {
            body['filter']['start_time'] = startTime;
            if (typeof body['filter']['start_time'] !== 'string') {
                body['filter']['start_time'] = body['filter']['start_time'].toISOString();
            }
        }
        if (endTime != null) {
            body['filter']['end_time'] = endTime.toISOString();
            if (typeof body['filter']['end_time'] !== 'string') {
                body['filter']['end_time'] = body['filter']['end_time'].toISOString();
            }
        }
        if (type != null) {
            body['filter']['type'] = type;
        }
        if (sortByTime != null) {
            body['sort']['time'] = sortByTime ? 1 : 0;
        }
        if (sortByType != null) {
            body['sort']['type'] = sortByType ? 1 : 0;
        }
        if (limit != null) {
            body['limit'] = limit;
        }
        if (offset != null) {
            body['offset'] = offset;
        }

        Logger.debug('POST request: get logs');
        Logger.debug(`Path: ${path}`);
        Logger.debug(`Body: ${JSON.stringify(body)}`);

        const result = await axios.post(path, body);
        return MapperService.mapLogsResponse(result.data);
    }

    async getStatisticsDataStructure(robotName, dbName) {
        const path = this._constructPath(`api/monitoring/structure/${robotName}/${dbName}`);

        Logger.debug('GET request: get statistics data structure');
        Logger.debug(`Path: ${path}`);

        const result = await axios.get(path);
        return MapperService.mapDataStructureResponse(result.data);
    }

    async getStatisticsDatabasesInfo(robotName) {
        const path = this._constructPath(`api/monitoring/databases_info/${robotName}`);

        Logger.debug('GET request: get statistics databases info');
        Logger.debug(`Path: ${path}`);

        const result = await axios.get(path);
        return MapperService.mapDatabasesInfoResponse(result.data);
    }

    async getStatisticsChartData(robotName, dbName, fieldName, limit = 1, offset = 0, startTime = null, endTime = null) {
        const path = this._constructPath(`api/monitoring/chart_data/${robotName}/${dbName}`);

        const body = {};
        body['filter'] = {}
        body['field_name'] = fieldName;

        if (startTime != null) {
            body['filter']['start_time'] = startTime;
            if (typeof body['filter']['start_time'] !== 'string') {
                body['filter']['start_time'] = body['filter']['start_time'].toISOString();
            }
        }
        if (endTime != null) {
            body['filter']['end_time'] = endTime;
            if (typeof body['filter']['end_time'] !== 'string') {
                body['filter']['end_time'] = body['filter']['end_time'].toISOString();
            }
        }
        if (limit != null) {
            body['limit'] = limit;
        }
        if (offset != null) {
            body['offset'] = offset;
        }

        Logger.debug('POST request: get statistics data');
        Logger.debug(`Path: ${path}`);
        Logger.debug(`Body: ${JSON.stringify(body)}`);

        const result = await axios.post(path, body);
        return MapperService.mapChartDataResponse(result.data);
    }

    async getStatisticsTableData(robotName, dbName, limit = 1, offset = 0, extended = false, filter = {}, sort = {}) {
        const path = this._constructPath(`api/monitoring/table_data/${robotName}/${dbName}`);

        const body = {};
        body['filter'] = {};
        body['sort'] = {};
        body['extended'] = extended;

        if (limit != null) {
            body['limit'] = limit;
        }
        if (offset != null) {
            body['offset'] = offset;
        }

        for (let filterElem in filter) {
            if (filter.hasOwnProperty(filterElem)) {
                const newName = filterElem.replace(/([A-Z])/g, '_$1').toLowerCase();
                body['filter'][newName] = filter[filterElem]
                if (['startTime', 'endTime'].includes(filterElem) && body['filter'][newName] && typeof body['filter'][newName] !== 'string') {
                    body['filter'][newName] = body['filter'][newName].toISOString();
                }
            }
        }

        for (let sortElem in sort) {
            if (sort.hasOwnProperty(sortElem)) {
                const newName = sortElem.replace(/([A-Z])/g, '_$1').toLowerCase();
                body['sort'][newName] = sort[sortElem]
            }
        }

        Logger.debug('POST request: get logs');
        Logger.debug(`Path: ${path}`);
        Logger.debug(`Body: ${JSON.stringify(body)}`);

        const result = await axios.post(path, body);
        return MapperService.mapTableDataResponse(result.data);
    }

    async getSystemInfo(extended = true) {
        const path = this._constructPath(`api/monitoring/system_info?extended=${extended}`);

        Logger.debug('GET request: get system info');
        Logger.debug(`Path: ${path}`);

        const result = await axios.get(path);
        return MapperService.mapSystemInfoResponse(result.data);
    }

    async getStatisticsMapsData(robotName, dbName) {
        const path = this._constructPath(`api/monitoring/maps_data/${robotName}/${dbName}`);

        Logger.debug('GET request: get statistics maps data');
        Logger.debug(`Path: ${path}`);

        const result = await axios.get(path);
        return MapperService.mapMapsDataResponse(result.data);
    }

    async uploadModuleArchive(formData) {
        const path = this._constructPath(`api/update_module`);

        Logger.debug('POST request: upload file');
        Logger.debug(`Path: ${path}`);

        const result = await axios.post(path, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        if (result.status !== 200) {
            Logger.error(`Can't upload file`)
        }
    }

    async uploadSSHArchive(formData) {
        const path = this._constructPath(`api/update_ssh`);
        const result = await axios.post(path, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        if (result.status === 200) {
            // TODO change answer format in backend
            return true;
        } else {
            Logger.error(result.data.errorInfo);
            throw new ServerExceptionModel(result.data.errorInfo, result.status);
        }
    }
}
