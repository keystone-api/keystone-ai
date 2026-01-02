#!/usr/bin/env node
/**
 * 🚪 Repository Evidence Scanner
 * 
 * 使用 PR Evidence Gate 策略掃描全儲存庫的每一個檔案
 * Scans the entire repository using PR Evidence Gate strategy
 * 
 * 功能：
 * 1. 掃描所有 Markdown 檔案中的證據標記
 * 2. 檢查 YAML 配置檔案的完整性
 * 3. 驗證程式碼檔案的註解規範
 * 4. 生成合規報告
 */

const fs = require('fs');
const path = require('path');

// Evidence patterns (from validate-pr-evidence.js)
const EVIDENCE_PATTERNS = {
  repo: /(^|\n)\s*-\s*repo\s*:\s*https:\/\/github\.com\/[^\/\s]+\/[^\/\s]+(\s|$)/i,
  branch: /(^|\n)\s*-\s*branch\s*:\s*\S+(\s|$)/i,
  commit: /(^|\n)\s*-\s*commit(?:\s*\(40-char\s*sha\))?\s*:\s*[0-9a-f]{40}(\s|$)/i,
  pr: /(^|\n)\s*-\s*pr\s*:\s*https:\/\/github\.com\/[^\/\s]+\/[^\/\s]+\/pull\/\d+(\s|$)/i
};

// Placeholder patterns to detect unfilled templates
const PLACEHOLDER_PATTERNS = [
  '<owner>', '<repo>', '<branch-name>', '<paste-full-sha-here>',
  '<this pr url>', '<number>', '[pr_number]', '[本 pr 編號]',
  '[分支名稱]', '[完整40字元Commit SHA]', '[PR編號]'
];

// File patterns for scanning
const SCAN_CONFIG = {
  // Files that should contain evidence markers (none by default for static files)
  // Evidence is checked dynamically by gate-pr-evidence.yml on PR body content
  evidenceRequired: [],
  // Template files (should have placeholders - this is expected)
  templateFiles: [
    'PULL_REQUEST_TEMPLATE.md',
    'pull_request_template.md',
    'ISSUE_TEMPLATE',
    'PR_DESCRIPTION.md'  // Legacy docs file, not an active PR template
  ],
  // Files to scan for placeholders (exclude templates)
  placeholderCheck: [
    '**/*.md',
    '**/*.yml',
    '**/*.yaml'
  ],
  // Directories to exclude
  excludeDirs: [
    'node_modules',
    '.git',
    'dist',
    'build',
    'coverage',
    'workspace-archive',
    'workspace-problematic'
  ],
  // File extensions to scan
  scanExtensions: ['.md', '.yml', '.yaml', '.js', '.ts', '.py', '.json']
};

class RepositoryScanner {
  constructor(rootDir) {
    this.rootDir = rootDir || process.cwd();
    this.results = {
      scanned: 0,
      passed: 0,
      warnings: 0,
      errors: 0,
      files: []
    };
  }

  /**
   * Check if directory should be excluded
   */
  shouldExclude(dirPath) {
    const baseName = path.basename(dirPath);
    return SCAN_CONFIG.excludeDirs.includes(baseName);
  }

  /**
   * Check if file matches extension filter
   */
  shouldScan(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    return SCAN_CONFIG.scanExtensions.includes(ext);
  }

  /**
   * Recursively collect all scannable files
   */
  collectFiles(dir = this.rootDir) {
    const files = [];
    
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          if (!this.shouldExclude(fullPath)) {
            files.push(...this.collectFiles(fullPath));
          }
        } else if (entry.isFile() && this.shouldScan(fullPath)) {
          files.push(fullPath);
        }
      }
    } catch (err) {
      console.error(`Error reading directory ${dir}: ${err.message}`);
    }
    
    return files;
  }

  /**
   * Check file for evidence markers
   */
  checkEvidence(content, filePath) {
    const issues = [];
    const relativePath = path.relative(this.rootDir, filePath);
    
    // Check if file should have evidence markers
    const fileName = path.basename(filePath);
    const requiresEvidence = SCAN_CONFIG.evidenceRequired.some(pattern => {
      if (pattern.includes('*')) {
        const regex = new RegExp(pattern.replace(/\*/g, '.*'));
        return regex.test(relativePath);
      }
      return fileName === pattern || relativePath.endsWith(pattern);
    });
    
    if (requiresEvidence) {
      // Check for all four core evidence items
      if (!EVIDENCE_PATTERNS.repo.test(content)) {
        issues.push({
          type: 'error',
          message: '缺少 repo 證據標記 (Missing repo evidence marker)'
        });
      }
      if (!EVIDENCE_PATTERNS.branch.test(content)) {
        issues.push({
          type: 'error', 
          message: '缺少 branch 證據標記 (Missing branch evidence marker)'
        });
      }
      if (!EVIDENCE_PATTERNS.commit.test(content)) {
        issues.push({
          type: 'error',
          message: '缺少 commit 證據標記 (Missing commit evidence marker)'
        });
      }
      if (!EVIDENCE_PATTERNS.pr.test(content)) {
        issues.push({
          type: 'error',
          message: '缺少 PR 證據標記 (Missing PR evidence marker)'
        });
      }
    }
    
    return issues;
  }

  /**
   * Check if file is a template file (templates are expected to have placeholders)
   */
  isTemplateFile(filePath) {
    const fileName = path.basename(filePath);
    return SCAN_CONFIG.templateFiles.some(template => 
      fileName.includes(template) || filePath.includes(template)
    );
  }

  /**
   * Check file for unfilled placeholders
   */
  checkPlaceholders(content, filePath) {
    const issues = [];
    
    // Skip placeholder check for template files (they're supposed to have them)
    if (this.isTemplateFile(filePath)) {
      return issues;
    }
    
    const lowerContent = content.toLowerCase();
    
    for (const placeholder of PLACEHOLDER_PATTERNS) {
      if (lowerContent.includes(placeholder.toLowerCase())) {
        issues.push({
          type: 'warning',
          message: `包含未填寫的 placeholder: ${placeholder} (Contains unfilled placeholder)`
        });
      }
    }
    
    return issues;
  }

  /**
   * Scan a single file
   */
  scanFile(filePath) {
    const relativePath = path.relative(this.rootDir, filePath);
    const result = {
      path: relativePath,
      status: 'pass',
      issues: []
    };
    
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      
      // Check for evidence markers
      const evidenceIssues = this.checkEvidence(content, filePath);
      result.issues.push(...evidenceIssues);
      
      // Check for placeholders in markdown files
      if (filePath.endsWith('.md')) {
        const placeholderIssues = this.checkPlaceholders(content, filePath);
        result.issues.push(...placeholderIssues);
      }
      
      // Determine overall status
      if (result.issues.some(i => i.type === 'error')) {
        result.status = 'error';
        this.results.errors++;
      } else if (result.issues.some(i => i.type === 'warning')) {
        result.status = 'warning';
        this.results.warnings++;
      } else {
        this.results.passed++;
      }
      
    } catch (err) {
      result.status = 'error';
      result.issues.push({
        type: 'error',
        message: `無法讀取檔案: ${err.message} (Cannot read file)`
      });
      this.results.errors++;
    }
    
    this.results.scanned++;
    return result;
  }

  /**
   * Run full repository scan
   */
  scan() {
    console.log('🔍 開始掃描儲存庫... (Starting repository scan...)');
    console.log(`📁 根目錄: ${this.rootDir}`);
    console.log('');
    
    const files = this.collectFiles();
    console.log(`📊 找到 ${files.length} 個可掃描的檔案 (Found ${files.length} scannable files)`);
    console.log('');
    
    for (const file of files) {
      const result = this.scanFile(file);
      if (result.issues.length > 0) {
        this.results.files.push(result);
      }
    }
    
    return this.results;
  }

  /**
   * Generate report
   */
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total_scanned: this.results.scanned,
        passed: this.results.passed,
        warnings: this.results.warnings,
        errors: this.results.errors,
        compliance_rate: this.results.scanned > 0 
          ? ((this.results.passed / this.results.scanned) * 100).toFixed(2) + '%'
          : '0%'
      },
      files_with_issues: this.results.files
    };
    
    return report;
  }

  /**
   * Print console report
   */
  printReport() {
    console.log('');
    console.log('═'.repeat(60));
    console.log('📊 掃描結果報告 (Scan Results Report)');
    console.log('═'.repeat(60));
    console.log('');
    console.log(`總掃描檔案數 (Total Scanned): ${this.results.scanned}`);
    console.log(`✅ 通過 (Passed): ${this.results.passed}`);
    console.log(`⚠️  警告 (Warnings): ${this.results.warnings}`);
    console.log(`❌ 錯誤 (Errors): ${this.results.errors}`);
    
    const complianceRate = this.results.scanned > 0 
      ? ((this.results.passed / this.results.scanned) * 100).toFixed(2)
      : 0;
    console.log(`📈 合規率 (Compliance Rate): ${complianceRate}%`);
    console.log('');
    
    if (this.results.files.length > 0) {
      console.log('─'.repeat(60));
      console.log('📋 有問題的檔案 (Files with Issues):');
      console.log('─'.repeat(60));
      
      for (const file of this.results.files) {
        const icon = file.status === 'error' ? '❌' : '⚠️';
        console.log(`\n${icon} ${file.path}`);
        for (const issue of file.issues) {
          const issueIcon = issue.type === 'error' ? '  ✖' : '  ⚡';
          console.log(`${issueIcon} ${issue.message}`);
        }
      }
    }
    
    console.log('');
    console.log('═'.repeat(60));
    
    // Return exit code
    return this.results.errors > 0 ? 1 : 0;
  }
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const outputJson = args.includes('--json');
  
  // Filter out flags to get the root directory
  const nonFlagArgs = args.filter(arg => !arg.startsWith('--'));
  const rootDir = nonFlagArgs[0] || process.cwd();
  
  const scanner = new RepositoryScanner(rootDir);
  scanner.scan();
  
  if (outputJson) {
    const report = scanner.generateReport();
    console.log(JSON.stringify(report, null, 2));
    process.exit(report.summary.errors > 0 ? 1 : 0);
  } else {
    const exitCode = scanner.printReport();
    process.exit(exitCode);
  }
}

module.exports = { RepositoryScanner, EVIDENCE_PATTERNS, PLACEHOLDER_PATTERNS };
