let LogModel = require('./LogModel').LogModel;

export class LogsResponse {
    constructor(count = 0, result = []) {
        this.count = count;
        this.result = result;
    }
}


