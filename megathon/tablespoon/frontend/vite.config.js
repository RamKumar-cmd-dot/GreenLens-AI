import {defineConfig} from 'vitest/config';
export default defineConfig({server:{proxy:{'/api':{target:'http://127.0.0.1:8000',rewrite:p=>p.replace(/^\/api/,'')}}},test:{environment:'jsdom',setupFiles:['./tests/setup.js']}});
